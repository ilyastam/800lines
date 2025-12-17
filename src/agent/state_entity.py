from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Generic, TypeVar, Any
from pydantic import BaseModel, Field

from agent.types import MutationIntent, FieldDiff

ContentType = TypeVar("ContentType")


class ValidationErrorHandlingMode(Enum):
    ignore = 'ignore'
    raise_exception = 'raise_exception'
    skip_merge = 'skip_merge'


class EntityMergeValidationError(Exception):
    pass


class Completable(ABC):
    @abstractmethod
    def is_completed(self) -> bool:
        pass


class BaseStateEntity(BaseModel, Generic[ContentType]):
    content: ContentType
    date_created_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), exclude=True)
    embedding: list[float] | None = Field(default=None, exclude=True)

    def is_completable(self):
        return isinstance(self.content, Completable)

    def is_completed(self):
        return self.is_completable() and self.content.is_completed()

    def update_content(self, diffs: list[FieldDiff]) -> 'BaseStateEntity':
        update_dict = {diff.field_name: diff.new_value for diff in diffs}
        self.content = self.content.model_copy(update=update_dict)
        return self

    @classmethod
    def merge(cls, current: 'BaseStateEntity' | None,
              intent: MutationIntent,
              on_validation_error: ValidationErrorHandlingMode = ValidationErrorHandlingMode.skip_merge) -> tuple['BaseStateEntity', MutationIntent]:
        validation_errors = current.validate_before_merge(intent) if current else []

        if validation_errors:
            intent_with_errors = intent.model_copy(update={"validation_errors": validation_errors})
            match on_validation_error:
                case ValidationErrorHandlingMode.raise_exception:
                    raise EntityMergeValidationError(f"Can't merge entity {current} with intent {intent} due to validation errors: {validation_errors}")
                case ValidationErrorHandlingMode.skip_merge:
                    return current, intent_with_errors.model_copy(update={"diffs": []})

        if current:
            return current.update_content(intent.diffs), intent

        update_dict = {diff.field_name: diff.new_value for diff in intent.diffs}
        new_entity = cls(content=cls.model_fields['content'].annotation(**update_dict))
        return new_entity, intent

    def validate_before_merge(self, intent: MutationIntent) -> list[str]:
        return []


class LlmParsedStateEntity(BaseStateEntity[ContentType]):

    #TODO : make this more abstract 
    @classmethod
    def model_json_schema(cls, **kwargs) -> dict[str, Any]:
        """Override to exclude embedding field from JSON schema"""
        schema = super().model_json_schema(**kwargs)
        # Remove embedding field from properties if it exists
        if "properties" in schema and "embedding" in schema["properties"]:
            del schema["properties"]["embedding"]
        # Remove from required fields if it exists
        if "required" in schema and "embedding" in schema["required"]:
            schema["required"].remove("embedding")
        return schema

    



