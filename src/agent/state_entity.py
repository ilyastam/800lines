from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import ClassVar, Generic, TypeVar, Any
from pydantic import BaseModel, Field, model_validator

from agent.state_storage.state_change import compare_entities, StateChange

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

    def merge(self, update: 'BaseStateEntity', on_validation_error: ValidationErrorHandlingMode = ValidationErrorHandlingMode.skip_merge) -> StateChange | None:
        state_change: StateChange | None = compare_entities(self, update, self.__class__.__name__)

        if state_change.validation_errors:
            match on_validation_error:
                case ValidationErrorHandlingMode.raise_exception:
                    raise EntityMergeValidationError(f"Can't merge entities {self} and {update} due to validation errors: {state_change.validation_errors}")
                case ValidationErrorHandlingMode.skip_merge:
                    return state_change.clear_changes()

        self.model_copy(update=update.model_dump(exclude_unset=True))
        return state_change

    def validate_before_merge(self, update: 'BaseStateEntity') -> list[str]:
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

    



