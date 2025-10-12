import datetime
from functools import wraps
import hashlib
import uuid
from collections import OrderedDict
import traceback
from .models import Interaction, InteractionRole, WorkflowStatus, WorkflowState as WorkflowStateModel
from typing import Callable, get_args, get_origin, Type, TypeVar, Any
import logging
logger = logging.getLogger(__name__)
import inspect
from pydantic.main import BaseModel

CacheValueT = TypeVar('CacheValueT', bound=BaseModel | Any)

def cached_step(_func=None, key_args: set[str] | None = None):
    # Support usage as @cached_step, @cached_step(), @cached_step({'a'}), or @cached_step(key_args={'a'})
    if _func is not None and not callable(_func) and key_args is None:
        key_args = _func
        _func = None

    def decorator(method):
        sig = inspect.signature(method)  # compute once at decoration time

        @wraps(method)
        def wrapper(self, *args, **kwargs):
            assert isinstance(self, DurableWorkflow), "cached_step must be used on an instance method of DurableWorkflow"

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

            cached_step_name = method.__name__
            arg_fingerprint_inputs = tuple((name, bound.arguments[name]) for name in selected_names) 
            arg_fingerprint = hash(arg_fingerprint_inputs)
            invocation_key = f"{cached_step_name}::{arg_fingerprint}"

            cached = self.get_cached_step_result(invocation_key)
            if cached is not None:
                return cached

            result = method(self, *args, **kwargs)
            self.set_cached_step_result(invocation_key, result)
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
        self.name = name
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
        raise NotImplementedError("Please implement the run method - this is like the most important part :)")

    def get_last_interaction_context_id(self) -> str | None:
        if self.interactions_count() <= 0:
            return None
        return self.get_interactions()[-1].get('context_id')

    def request_input(self, input_prompt: str):
        state: WorkflowStateModel = self.get_local_state()

        if state.status == WorkflowStatus.INPUT_SET_BUT_NOT_CONSUMED:
            interaction: Interaction = state.interactions[-1]
            assert interaction.role == InteractionRole.USER
            state.status = WorkflowStatus.RUNNING
            return interaction.content

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

        state.status = WorkflowStatus.INPUT_SET_BUT_NOT_CONSUMED
        state.interactions.append(Interaction(
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            role=InteractionRole.USER,
            content=value
        ))

    def invocation_key(self) -> str:
        """
        Compute a unique, deterministic fingerprint for this invocation by hashing
        the entire remaining call stack (from the first DurableWorkflow-owned frame
        down to the bottom). No additional params required.

        Notes:
        - Using the whole tail of the stack creates a fully unique invocation fingerprint.
        - We anchor at the first frame whose `self` is a DurableWorkflow (or subclass)
          to attribute the call to the workflow cached_step context before including all
          deeper frames in the digest.
        """
        stack = inspect.stack()
        try:
            # Find the first frame that belongs to a DurableWorkflow instance
            start_idx = 1
            func_label = "unknown"

            # Build a canonical representation for all frames from start_idx to the end
            frames_repr: list[str] = []
            for fi in stack[1:]:
                f = fi.frame
                module = f.f_globals.get("__name__", "")
                func = fi.function
                file = fi.filename
                line = fi.lineno
                owner = f.f_locals.get("self")
                cls_name = type(owner).__name__ if isinstance(owner, DurableWorkflow) else ""
                frames_repr.append(f"{module}:{cls_name}:{func}:{file}:{line}")

            # Fallback if nothing captured (should be rare)
            if not frames_repr:
                frames_repr = [f"{fi.function}@{fi.filename}:{fi.lineno}" for fi in stack[1:]]

            serialized = "||".join(frames_repr)
            digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]
            return f"{self.state_prefix}::{func_label}::{digest}"
        finally:
            # Help GC by dropping frame references
            del stack

    def full_cache_key_for_input(self) -> str:
        """
        Backwards-compatible alias for a fully unique invocation fingerprint.
        """
        return self.invocation_key()

    def get_status(self) -> WorkflowStatus:
        return self.get_local_state().status

    def complete_workflow(self):
        self.get_local_state().status = WorkflowStatus.COMPLETED

    @property
    def is_running(self) -> bool:
        return self.get_local_state().status in {WorkflowStatus.RUNNING,  WorkflowStatus.INPUT_SET_BUT_NOT_CONSUMED}

    def is_waiting_for_input(self) -> bool:
        return self.get_local_state().status == WorkflowStatus.WAITING_FOR_INPUT

    def get_local_state(self) -> WorkflowStateModel:
        assert self.state_prefix in self.state, f"State has not been initialized properly for {self.state_prefix} state_prefix"
        return self.state[self.state_prefix]

    def get_cached_step_result(self, cached_step_result_key: str) -> Any | None:
        return self.get_local_state().results.get(cached_step_result_key)

    def set_cached_step_result(self, cached_step_result_key: str, value: Any):
        assert value is not None, "cached_step result cannot be None"
        self.get_local_state().results[cached_step_result_key] = value

    def get_inc_attempt(self, key: str, default_val: int = 1) -> int:
        value: int = self.get_cache_value(key, int) or default_val
        self.set_cache_value(key, value + 1)
        return value

    @staticmethod
    def compute_hash(inp) -> str:
        sha256_hash = hashlib.sha256(inp.encode()).hexdigest()
        return sha256_hash


"""
TODO:
test state injection
"""


class W1(DurableWorkflow):
    def __init__(self):
        super().__init__()
        pass

    def run(self):
        print(self.test1(cache_key='foo'))
        self.complete_workflow()

    @cached_step 
    def test1(self, cache_key=None) -> Any:
        return "result"


if __name__ == '__main__':
    w1 = W1()
    w1.run()
    print(w1.state)




