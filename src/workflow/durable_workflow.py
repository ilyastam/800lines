import datetime
from functools import wraps
import hashlib
import uuid
from collections import OrderedDict
import traceback
from models import Interaction, InteractionRole, WorkflowStatus, WorkflowState as WorkflowStateModel
from typing import Callable, get_args, get_origin, Type, TypeVar, Any
import logging
logger = logging.getLogger(__name__)
import inspect
from pydantic.main import BaseModel

CacheValueT = TypeVar('CacheValueT', bound=BaseModel | Any)

def step(_func=None, key_args: set[str] | None = None):
    # Support usage as @step, @step(), @step({'a'}), or @step(key_args={'a'})
    if _func is not None and not callable(_func) and key_args is None:
        key_args = _func
        _func = None

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

            step_name = method.__name__
            arg_fingerprint = hash(tuple((name, bound.arguments[name]) for name in selected_names))
            invocation_key = f"{step_name}::{arg_fingerprint}"

            cached = self.get_step_result(invocation_key)
            if cached is not None:
                return cached

            print(f"Step {step_name} key={invocation_key}")
            self.get_local_state().step_in_progress = invocation_key
            result = method(self, *args, **kwargs)
            self.set_step_result(invocation_key, result)
            self.get_local_state().step_in_progress = None
            return result

        return wrapper

    if _func is None:
        return decorator
    else:
        return decorator(_func)

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
        return len(self.get_local_state().interactions)

    def get_interactions(self) -> list[Interaction]:
        return self.get_local_state().interactions

    def run(self):
        raise NotImplementedError()

    def get_last_interaction_context_id(self) -> str | None:
        if self.interactions_count() <= 0:
            return None
        return self.get_interactions()[-1].get('context_id')


    @step({'input_key'})
    def request_input(self, input_prompt: str, input_key: str):
        state: WorkflowStateModel = self.get_local_state()

        if state.status == WorkflowStatus.WAITING_FOR_INPUT:
            interaction = state.interactions[-1]
            assert interaction.role == InteractionRole.SYSTEM, "workflow is waiting for input, but last interaction is not from the system"
        else:
            state.status = WorkflowStatus.WAITING_FOR_INPUT
            interaction = Interaction(
                timestamp=datetime.datetime.now(datetime.timezone.utc),
                role=InteractionRole.SYSTEM,
                content=input_prompt
            ) 
            state.interactions.append(interaction)   

        raise InputRequested(
            input_prompt=interaction.content
        )

    def set_input(self, value: Any):
        assert value is not None, "input value cannot be None"
        state: WorkflowStateModel = self.get_local_state()
        assert state.status == WorkflowStatus.WAITING_FOR_INPUT, "Can't set result when system is not waiting for input"

        self.set_step_result(state.step_in_progress, value)
        state.status = WorkflowStatus.RUNNING
        state.step_in_progress = None
        state.interactions.append(Interaction(
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            role=InteractionRole.USER,
            content=value
        ))

    def get_status(self):
        return self.get_local_state().status

    def complete_workflow(self):
        self.get_local_state().status = WorkflowStatus.COMPLETED

    @property
    def is_running(self):
        return self.get_local_state().status == WorkflowStatus.RUNNING

    def is_waiting_for_input(self):
        return self.get_local_state().status == WorkflowStatus.WAITING_FOR_INPUT

    def get_local_state(self) -> WorkflowStateModel:
        assert self.state_prefix in self.state, f"State has not been initialized properly for {self.state_prefix} state_prefix"
        return self.state[self.state_prefix]

    def get_step_result(self, step_result_key: str) -> Any | None:
        return self.get_local_state().results.get(step_result_key)

    def set_step_result(self, step_result_key: str, value: Any):
        assert value is not None, "step result cannot be None"
        self.get_local_state().results[step_result_key] = value

    def get_inc_attempt(self, key: str, default_val: int = 1) -> int:
        value: int = self.get_cache_value(key, int) or default_val
        self.set_cache_value(key, value + 1)
        return value

    @staticmethod
    def compute_hash(inp):
        sha256_hash = hashlib.sha256(inp.encode()).hexdigest()
        return sha256_hash



class W1(DurableWorkflow):
    def __init__(self):
        super().__init__()
        pass

    def run(self):
        print(self.test1(cache_key='foo'))
        self.complete_workflow()

    @step 
    def test1(self, cache_key=None) -> Any:
        return "result"


if __name__ == '__main__':
    w1 = W1()
    w1.run()
    print(w1.state)




