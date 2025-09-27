from __future__ import annotations

from collections import OrderedDict
import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class WorkflowStatus(str, Enum):
    RUNNING = "running"
    WAITING_FOR_INPUT = "waiting_for_input"
    INPUT_SET_BUT_NOT_CONSUMED = "input_set_but_not_consumed"
    COMPLETED = "completed"
    


class WorkflowState(BaseModel):
    name: str | None = None
    status: WorkflowStatus = WorkflowStatus.RUNNING
    input_prompt: str | None = None
    results: OrderedDict[str, Any] = Field(default_factory=OrderedDict)
    invocation_sequence: list[str] = Field(default_factory=list)  
    interactions: list[Interaction] = Field(default_factory=list)

    # Coerce results to OrderedDict when deserializing from any dict
    @field_validator("results", mode="before")
    @classmethod
    def _coerce_results(cls, v: Any) -> OrderedDict[str, Any]:
        if v is None:
            return OrderedDict()
        if isinstance(v, OrderedDict):
            return v
        if isinstance(v, dict):
            return OrderedDict(v)
        return v

    # Dict-like access compatibility
    def __getitem__(self, key: str) -> Any:
        # Prefer attribute access; fall back to internal dict for extras
        if hasattr(self, key):
            return getattr(self, key)
        return self.__dict__[key]

    def __setitem__(self, key: str, value: Any) -> None:
        # With extra=allow this will also store unknown keys
        setattr(self, key, value)

    def get(self, key: str, default: Any = None) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        return self.__dict__.get(key, default)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key) or key in self.__dict__
    

class InteractionRole(str, Enum):
    SYSTEM = "system"
    USER = "user"

class Interaction(BaseModel):
    timestamp: datetime.datetime
    role: InteractionRole
    content: Any | str
    