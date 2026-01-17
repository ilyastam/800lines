from __future__ import annotations

from pydantic import BaseModel, Field, field_serializer

from agent.state.entity.actor.base_actor import BaseActor
from agent.state.entity.state_entity import BaseStateEntity
from agent.state.entity.types import FieldDiff


class LlmStateDiff(BaseModel):
    """LLM-parseable state diff with string-based entity class name."""
    entity_class_name: str = Field(description="Name of the entity class that user intends to mutate.")
    entity_ref: str | None = Field(default=None, description="Reference to the specific entity that user intends to mutate. Can be None.")
    diffs: list[FieldDiff] = Field(description="List of field changes")


class LlmStateDiffs(BaseModel):
    """LLM response format for state diffs."""
    diffs: list[LlmStateDiff] = Field(default_factory=list, description="All state diffs expressed by user in their last interaction")


class LlmTask(BaseModel):
    """LLM-parseable task representation."""
    task: str = Field(description="Description of task user wants agent to perform")


class LlmParseResult(BaseModel):
    """LLM response format that captures both state diffs and tasks."""
    diffs: list[LlmStateDiff] = Field(default_factory=list, description="All state diffs expressed by user in their last interaction")
    tasks: list[LlmTask] = Field(default_factory=list, description="All tasks expressed by user in their last interaction")


class StateDiff(BaseModel):
    entity_class: type[BaseStateEntity] = Field(description="Entity class that user intends to mutate.")
    entity_ref: str | None = Field(default=None, description="Reference to the specific entity that user intends to mutate. Can be None.")
    diffs: list[FieldDiff] = Field(description="List of field changes")
    validation_errors: list[str] = Field(default_factory=list, description="Validation errors encountered during merge")
    actor: BaseActor | None = Field(default=None, description="Actor who initiated this mutation")

    model_config = {"arbitrary_types_allowed": True}

    @field_serializer('entity_class')
    def serialize_entity_class(self, v: type[BaseStateEntity]) -> str:
        return v.__name__
