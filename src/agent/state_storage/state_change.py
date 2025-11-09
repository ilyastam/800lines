from typing import TypeVar, Generic

from pydantic import BaseModel, Field

ContextRef = TypeVar("ContextRef")


class FieldChange(BaseModel):
    field_name: str
    from_value: str
    to_value: str


class StateChange(BaseModel, Generic[ContextRef]):
    context_ref: ContextRef
    changes: list[FieldChange] = Field(default_factory=list)