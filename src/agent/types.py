from datetime import datetime

from pydantic import BaseModel, Field

Primitive = str | int | float | bool | datetime | None


class ModelContext(BaseModel):
    """
    Data that represents user intent and that can be changed
    upon user's request.
    """
    model_class: str
    model_refs: list[str] | None = None


class FieldDiff(BaseModel):
    field_name: str = Field(description="Name of the field to modify")
    new_value: Primitive | list[Primitive] | dict[str, Primitive] = Field(description="New value for the field")


class MutationIntent(BaseModel):
    model_class_name: str = Field(description="Name of the model class that user intents to mutate.")
    model_ref: str | None = Field(default=None, description="Reference to the specific model that user intends to mutate. Can be None.")
    diffs: list[FieldDiff] = Field(description="List of field changes")
    validation_errors: list[str] = Field(default_factory=list, description="Validation errors encountered during merge")


class MutationIntents(BaseModel):
    intents: list[MutationIntent] = Field(default_factory=list, description="All mutation intents expressed by user in their last interaction")


