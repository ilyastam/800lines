import datetime
from functools import wraps
import hashlib
import uuid
from collections import OrderedDict
import traceback
from .models import WorkflowStatus, WorkflowState as WorkflowStateModel
from typing import Callable, get_args, get_origin, Type, TypeVar, Any
import logging
logger = logging.getLogger(__name__)
import inspect
from pydantic.main import BaseModel

CacheValueT = TypeVar('CacheValueT', bound=BaseModel | Any)

def get_serialized_stack_trace():
    stack_trace = traceback.extract_stack()
    function_names = [frame[2] for frame in stack_trace[:-2]]  # Exclude the current function
    serialized_trace = "::".join(function_names)
    return serialized_trace.replace("<module>::", "").replace("::__wrapper_func__", "")


def get_previous_function_name():
    stack = traceback.extract_stack()
    traceback_obj = traceback.extract_stack()[-3]  # accounts for wrapper function
    return traceback_obj.name


class InputRequested(Exception):
    def __init__(self, input_prompt=None, context_id: str | None = None):
        self.user_prompt = input_prompt
        self.context_id = context_id

class DurableWorkflow(object):
    def __init__(self, name: str | None = None, state_prefix: str | None = None, state: dict[str, WorkflowStateModel] | None = None):
        self.state_prefix = f"{type(self).__name__}"
        if state_prefix:
            self.state_prefix += f"::{state_prefix}"

        if state:
            self.state = state
        else:
            self.state = {self.state_prefix: WorkflowStateModel(name=name)}

    def interactions_count(self):
        return len(self.state['interactions'])

    def get_interactions(self) -> list[dict[str, str]]:
        return self.state['interactions']

    def get_expected_user_prompts_count(self) -> int:
        raise NotImplementedError()

    def get_current_user_prompts_count(self) -> int:
        return len(list(filter(lambda i: 'user' in i, self.get_interactions())))

    """
    When called in context of request input - step will be already part of the stack trace
    """
    def get_invocation_key(self, cache_key=None, step_name=None):
        state_prefix = object.__getattribute__(self, 'state_prefix')
        invocation_key = f"{state_prefix}"
        if step_name:
            invocation_key += f"::{step_name}"
        if cache_key:
            invocation_key += f"::{cache_key}"
        return invocation_key

    def __getattribute__(self, name):
        attr = object.__getattribute__(self, name)
        if not callable(attr) or not attr.__name__.startswith('step'):
            return attr

        def __wrapper_func__(*args, **kwargs):
            if 'cache_key' in kwargs:
                invocation_key = self.get_invocation_key(cache_key=kwargs.get('cache_key'), step_name=attr.__name__)
                logger.debug(invocation_key)

                if invocation_key in self.state['results'] and self.state['results'][invocation_key] and 'result' in self.state['results'][invocation_key]:
                    logger.debug("  Returning cached result")
                    return self.deserialize_result(attr, self.state['results'][invocation_key]['result'])

                if self.state['status'] == WorkflowStatus.WAITING_FOR_INPUT:
                    last_interaction = self.state['interactions'][-1]
                    raise InputRequested(
                        input_prompt=last_interaction['system'],
                        mode=last_interaction['mode'],
                        max_duration_sec=last_interaction['max_duration_sec'],
                    )

                logger.debug("  Computing result")
                self.state['invocation_sequence'].append(invocation_key)
                result = attr(*args, **kwargs)
                self.state['results'][invocation_key] = {'result': self.serialize_result(result)}
                self.state['invocation_sequence'].append(invocation_key)
                return result
            else:
                logger.warning(f"Warn: {name} called without a cache_key - recomputing result")
                return attr(*args, **kwargs)

        if callable(attr):
            return __wrapper_func__
        else:
            return attr

    def run(self):
        raise NotImplementedError()

    def get_last_interaction_context_id(self) -> str | None:
        if self.interactions_count() <= 0:
            return None
        return self.get_interactions()[-1].get('context_id')

    def request_input(self, cache_key,
                      input_prompt=None,
                      mode: str = 'voice',
                      max_duration_sec: int = 5 * 60,
                      context_id: str | None = None):
        assert cache_key, "cache_key must be set for the input request"
        self.state['status'] = WorkflowStatus.WAITING_FOR_INPUT
        full_cache_key = self.get_invocation_key(cache_key=cache_key, step_name=get_previous_function_name())
        self.state['step_awaiting_input'] = full_cache_key
        self.state['user_prompt'] = input_prompt
        used_context_id = context_id or str(uuid.uuid4())
        self.state['interactions'].append({
            'system': input_prompt,
            'cache_key': full_cache_key,
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'mode': mode,
            'max_duration_sec': max_duration_sec,
            'context_id': used_context_id,
            'role': 'system',
            'content': input_prompt
        })
        raise InputRequested(input_prompt=input_prompt, mode=mode, max_duration_sec=max_duration_sec, context_id=used_context_id)

    def set_input(self, value: Any, context_id: str | None = None):
        assert self.state['step_awaiting_input'], "No step is awaiting input"
        # if self.get_last_interaction_context_id() != context_id:
        #     raise Exception("Response doesn't correspond to question")

        full_cache_key = self.state['step_awaiting_input']
        self.state['results'][full_cache_key] = {'result': value}
        self.state['status'] = WorkflowStatus.RUNNING
        self.state['step_awaiting_input'] = None
        self.state['user_prompt'] = None
        self.state['interactions'].append({
            'user': value,
            'cache_key': full_cache_key,
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'context_id': context_id,
            'role': 'user',
            'content': value
        })

    def get_status(self):
        return self.state['status']

    def complete_workflow(self):
        self.state['state_values'][self.state_prefix] = False
        if not any(self.state['state_values'].values()):
            self.state['status'] = WorkflowStatus.COMPLETED

    @property
    def is_running(self):
        return self.state['state_values'][self.state_prefix]

    def is_waiting_for_input(self):
        return self.state['status'] == WorkflowStatus.WAITING_FOR_INPUT

    def get_local_state(self) -> WorkflowStateModel:
        assert self.state_prefix in self.state, f"State has not been initialized properly for {self.state_prefix} state_prefix"
        return self.state[self.state_prefix]

    def get_step_result(self, step_result_key: str) -> Any | None:
        return self.get_local_state().results.get(step_result_key)

    def set_step_result(self, step_result_key: str, value: Any):
        assert value, "step result cannot be None"
        self.get_local_state().results[step_result_key] = value

    def get_inc_attempt(self, key: str, default_val: int = 1) -> int:
        value: int = self.get_cache_value(key, int) or default_val
        self.set_cache_value(key, value + 1)
        return value

    @staticmethod
    def compute_hash(inp):
        sha256_hash = hashlib.sha256(inp.encode()).hexdigest()
        return sha256_hash


def step(key_args: set[str] | None):
    def decorator(method):
        sig = inspect.signature(method)  # compute once at decoration time

        @wraps(method)
        def wrapper(self, *args, **kwargs):
            # Bind arguments to parameter names and include defaults
            bound = sig.bind(self, *args, **kwargs)
            bound.apply_defaults()

            # Select which argument names to include in the cache key
            if key_args is None:
                selected_names = [name for name in bound.arguments.keys() if name != "self"]
            else:
                missing = [name for name in key_args if name not in bound.arguments]
                if missing:
                    raise Exception(f"Missing required argument(s) for cache key: {', '.join(missing)}")
                # Preserve parameter order while filtering to requested names
                selected_names = [name for name in sig.parameters.keys() if name in key_args and name != "self"]

            # Ensure all selected argument values are hashable
            for name in selected_names:
                value = bound.arguments[name]
                try:
                    hash(value)
                except TypeError:
                    raise Exception(f"Argument '{name}' with value of type {type(value).__name__} is not hashable")

            assert isinstance(self, DurableWorkflow)

            # Compute a deterministic hash based on (name, value) pairs in parameter order
            step_result_key = hash(tuple((name, bound.arguments[name]) for name in selected_names))

            step_resut = self.get_step_result(step_result_key)
            if step_resut:
                return step_resut

            print(f"Step {method.__name__} cache_key={cache_key}")
            result = method(self, *args, **kwargs)
            self.set_step_result(step_result_key, result)
            return result

        return wrapper
    return decorator


class Foo(BaseModel):
    bar: str


class W1(Workflow):
    def __init__(self):
        super().__init__()
        pass

    def run(self):
        print(self.step_test1(cache_key='moo'))
        print(self.step_test1(cache_key='moo'))
        self.complete_workflow()

    def step_test1(self, cache_key=None) -> Foo:
        return Foo(bar='zoo')


if __name__ == '__main__':
    w1 = W1()
    w1.run()
    print(w1.cache)




