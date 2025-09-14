import datetime
import hashlib
import uuid
from collections import OrderedDict
import traceback
from enum import Enum
from typing import Optional, List, Callable, get_args, get_origin, Type, TypeVar, Dict, Any, Union
import logging
logger = logging.getLogger(__name__)
import inspect
from pydantic.main import BaseModel

CacheValueT = TypeVar('CacheValueT', bound=Union[BaseModel, Any])

def get_serialized_stack_trace():
    stack_trace = traceback.extract_stack()
    function_names = [frame[2] for frame in stack_trace[:-2]]  # Exclude the current function
    serialized_trace = "::".join(function_names)
    return serialized_trace.replace("<module>::", "").replace("::__wrapper_func__", "")


def get_previous_function_name():
    stack = traceback.extract_stack()
    traceback_obj = traceback.extract_stack()[-3]  # accounts for wrapper function
    return traceback_obj.name


class WorkflowState(str, Enum):
    RUNNING = "running"
    WAITING_FOR_INPUT = "waiting_for_input"
    COMPLETED = "completed"


class InputRequested(Exception):
    def __init__(self, input_prompt=None, context_id: str | None = None):
        self.user_prompt = input_prompt
        self.context_id = context_id


class Workflow(object):
    def __init__(self, name: Optional[str] = None, cache_prefix: str = None, cache: Dict[str, Any] = None):
        self.cache_prefix = f"{type(self).__name__}"
        if cache_prefix:
            self.cache_prefix += f"::{cache_prefix}"

        if cache:
            self.cache = cache
            if 'results' in self.cache:
                self.cache['results'] = OrderedDict(self.cache['results'])
            if 'cache_sequence' not in self.cache:
                self.cache['cache_sequence'] = []
            if 'interactions' not in self.cache:
                self.cache['interactions'] = []
            if self.cache_prefix not in self.cache['cache_instances']:
                self.cache['cache_instances'][self.cache_prefix] = True

        else:
            self.cache: Dict[str, Any] = {
                'name': name,
                'results': OrderedDict({}),
                'state': WorkflowState.RUNNING,
                'step_awaiting_input': None,
                'user_prompt': None,
                'grade': None,
                'interactions': [],
                'cache_sequence': [],
                'models': {},
                'cache_instances': {
                    self.cache_prefix: True
                },
            }

    def interactions_count(self):
        return len(self.cache['interactions'])

    def get_interactions(self) -> List[Dict[str, str]]:
        return self.cache['interactions']

    def get_expected_user_prompts_count(self) -> int:
        raise NotImplementedError()

    def get_current_user_prompts_count(self) -> int:
        return len(list(filter(lambda i: 'user' in i, self.get_interactions())))

    """
    When called in context of request input - step will be already part of the stack trace
    """
    def get_invocation_key(self, cache_key=None, step_name=None):
        cache_prefix = object.__getattribute__(self, 'cache_prefix')
        invocation_key = f"{cache_prefix}"
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

                if invocation_key in self.cache['results'] and self.cache['results'][invocation_key] and 'result' in self.cache['results'][invocation_key]:
                    logger.debug("  Returning cached result")
                    return self.deserialize_result(attr, self.cache['results'][invocation_key]['result'])

                if self.cache['state'] == WorkflowState.WAITING_FOR_INPUT:
                    last_interaction = self.cache['interactions'][-1]
                    raise InputRequested(
                        input_prompt=last_interaction['system'],
                        mode=last_interaction['mode'],
                        max_duration_sec=last_interaction['max_duration_sec'],
                    )

                logger.debug("  Computing result")
                self.cache['cache_sequence'].append(invocation_key)
                result = attr(*args, **kwargs)
                self.cache['results'][invocation_key] = {'result': self.serialize_result(result)}
                self.cache['cache_sequence'].append(invocation_key)
                return result
            else:
                logger.warning(f"Warn: {name} called without a cache_key - recomputing result")
                return attr(*args, **kwargs)

        if callable(attr):
            return __wrapper_func__
        else:
            return attr

    @staticmethod
    def deserialize_result(func: Callable, result: Dict[str, Any]) -> Dict[str, Any] | BaseModel | List[BaseModel | Any]:
        ret_type = inspect.signature(func).return_annotation
        if hasattr(ret_type, '__origin__') and get_origin(ret_type) is Optional:
            ret_type = get_args(ret_type)[0]

        elif hasattr(ret_type, '__origin__') and get_origin(ret_type) is list:
            internal_type = get_args(ret_type)[0]

            # Process each item in the list if it's a subclass of BaseModel
            if issubclass(internal_type, BaseModel):
                return [internal_type.model_validate(item) for item in result]

            return result

        if issubclass(ret_type, BaseModel):
            return ret_type.model_validate(result)
        return result

    @staticmethod
    def serialize_result(result: Any):
        if isinstance(result, list):
            # Serialize each BaseModel in the list
            return [item.model_dump() if isinstance(item, BaseModel) else item for item in result]

        if isinstance(result, BaseModel):
            return result.model_dump()
        return result

    def run(self):
        raise NotImplementedError()

    def get_last_interaction_context_id(self) -> Optional[str]:
        if self.interactions_count() <= 0:
            return None
        return self.get_interactions()[-1].get('context_id')

    def request_input(self, cache_key,
                      user_prompt=None,
                      mode: str = 'voice',
                      max_duration_sec: int = 5 * 60,
                      context_id: Optional[str] = None):
        assert cache_key, "cache_key must be set for the input request"
        self.cache['state'] = WorkflowState.WAITING_FOR_INPUT
        full_cache_key = self.get_invocation_key(cache_key=cache_key, step_name=get_previous_function_name())
        self.cache['step_awaiting_input'] = full_cache_key
        self.cache['user_prompt'] = user_prompt
        used_context_id = context_id or str(uuid.uuid4())
        self.cache['interactions'].append({
            'system': user_prompt,
            'cache_key': full_cache_key,
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'mode': mode,
            'max_duration_sec': max_duration_sec,
            'context_id': used_context_id,
            'role': 'system',
            'content': user_prompt
        })
        raise InputRequested(input_prompt=user_prompt, mode=mode, max_duration_sec=max_duration_sec, context_id=used_context_id)

    def set_input(self, value, mode: str = 'voice', response_file: Optional[str] = None, context_id: str | None = None):
        assert self.cache['step_awaiting_input'], "No step is awaiting input"
        # if self.get_last_interaction_context_id() != context_id:
        #     raise Exception("Response doesn't correspond to question")

        full_cache_key = self.cache['step_awaiting_input']
        self.cache['results'][full_cache_key] = {'result': value}
        self.cache['state'] = WorkflowState.RUNNING
        self.cache['step_awaiting_input'] = None
        self.cache['user_prompt'] = None
        self.cache['interactions'].append({
            'user': value,
            'cache_key': full_cache_key,
            'mode': mode,
            'response_file': response_file,
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'context_id': context_id,
            'role': 'user',
            'content': value
        })

    def get_state(self):
        return self.cache['state']

    def complete_workflow(self):
        self.cache['cache_instances'][self.cache_prefix] = False
        if not any(self.cache['cache_instances'].values()):
            self.cache['state'] = WorkflowState.COMPLETED

    @property
    def is_running(self):
        return self.cache['cache_instances'][self.cache_prefix]

    def is_waiting_for_input(self):
        return self.cache['state'] == WorkflowState.WAITING_FOR_INPUT

    def get_result_key(self):
        return f"{self.cache_prefix}::workflow_result" if self.cache_prefix else "workflow_result"

    def set_result(self, result):
        self.cache[self.get_result_key()] = self.serialize_result(result)

    def get_result(self):
        if self.is_running:
            self.run()
        return self.cache.get(self.get_result_key())

    def get_full_cache_key(self, key: str) -> str:
        full_key = f'{self.cache_prefix}::{key}'
        return full_key

    def set_cache_value(self, key: str, value: Any) -> None:
        self.cache[self.get_full_cache_key(key)] = self.serialize_result(value)

    def get_cache_value(self, key: str, type_def: Type[CacheValueT]) -> CacheValueT:
        # Retrieve the serialized value from the cache
        value = self.cache.get(self.get_full_cache_key(key))
        if value is None:
            return None

        if issubclass(type_def, BaseModel):
            parsed_value = type_def.model_validate(value)
            return parsed_value
        else:
            # For primitive types, ensure the value is of the expected type
            if not isinstance(value, type_def):
                raise TypeError(f"Expected type {type_def}, but got {type(value)}.")
            return value

    def get_inc_attempt(self, key: str, default_val: int = 1) -> int:
        value: int = self.get_cache_value(key, int) or default_val
        self.set_cache_value(key, value + 1)
        return value

    def get_interactions_by_step_and_role(self, step_method: str, role: str, cache_key: str | None):
        assert step_method in self.__class__.__dict__ and callable(self.__class__.__dict__[step_method]), \
            f"{step_method} doesn't exist in {self.__class__}"

        invocation_key: str = self.get_invocation_key(cache_key=cache_key, step_name=step_method)
        interactions: List[Dict[str, str]] = self.get_interactions()
        ret: List[Dict[str, str]] = []
        for interaction in interactions:
            if interaction.get('cache_key') == invocation_key and interaction.get('role') == role:
                ret.append(interaction)

        return ret

    @staticmethod
    def compute_hash(inp):
        sha256_hash = hashlib.sha256(inp.encode()).hexdigest()
        return sha256_hash


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




