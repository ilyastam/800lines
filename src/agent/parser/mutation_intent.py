from __future__ import annotations

from pydantic import BaseModel, Field, field_serializer

from agent.state.entity.actor.base_actor import BaseActor
from agent.state.entity.state_entity import BaseStateEntity
from agent.state.entity.types import FieldDiff


class LlmMutationIntent(BaseModel):
    """LLM-parseable mutation intent with string-based entity class name."""
    entity_class_name: str = Field(description="Name of the entity class that user intends to mutate.")
    entity_ref: str | None = Field(default=None, description="Reference to the specific entity that user intends to mutate. Can be None.")
    diffs: list[FieldDiff] = Field(description="List of field changes")


class LlmMutationIntents(BaseModel):
    """LLM response format for mutation intents."""
    intents: list[LlmMutationIntent] = Field(default_factory=list, description="All mutation intents expressed by user in their last interaction")


class MutationIntent(BaseModel):
    entity_class: type[BaseStateEntity] = Field(description="Entity class that user intends to mutate.")
    entity_ref: str | None = Field(default=None, description="Reference to the specific entity that user intends to mutate. Can be None.")
    diffs: list[FieldDiff] = Field(description="List of field changes")
    validation_errors: list[str] = Field(default_factory=list, description="Validation errors encountered during merge")
    actor: BaseActor | None = Field(default=None, description="Actor who initiated this mutation")

    model_config = {"arbitrary_types_allowed": True}

    @field_serializer('entity_class')
    def serialize_entity_class(self, v: type[BaseStateEntity]) -> str:
        return v.__name__
