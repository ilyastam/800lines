from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from agent.state.entity.actor.base_actor import BaseActor

Primitive = str | int | float | bool | datetime | None


class EntityContext(BaseModel):
    """
    Data that represents user intent and that can be changed
    upon user's request.
    """
    entity_class_name: str
    entity_schema: dict[str, Any] | None = None
    entity_refs: list[str] | None = None


class FieldDiff(BaseModel):
    field_name: str = Field(description="Name of the field to modify")
    new_value: Primitive | list[Primitive] | dict[str, Primitive] = Field(description="New value for the field")


class MutationIntent(BaseModel):
    entity_class_name: str = Field(description="Name of the entity class that user intends to mutate.")
    entity_ref: str | None = Field(default=None, description="Reference to the specific entity that user intends to mutate. Can be None.")
    diffs: list[FieldDiff] = Field(description="List of field changes")
    validation_errors: list[str] = Field(default_factory=list, description="Validation errors encountered during merge")
    actor: BaseActor | None = Field(default=None, description="Actor who initiated this mutation")


class MutationIntents(BaseModel):
    intents: list[MutationIntent] = Field(default_factory=list, description="All mutation intents expressed by user in their last interaction")


