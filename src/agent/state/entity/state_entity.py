from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from types import UnionType
from typing import Any, ClassVar, get_origin, get_args, Union, TYPE_CHECKING
from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo

from agent.state.entity.actor.base_actor import BaseActor
from agent.state.entity.types import FieldDiff

if TYPE_CHECKING:
    from agent.parser.state_diff import StateDiff


class ValidationErrorHandlingMode(Enum):
    ignore = 'ignore'
    raise_exception = 'raise_exception'
    skip_merge = 'skip_merge'


class EntityMergeValidationError(Exception):
    pass


class BaseStateEntity(BaseModel):
    _metadata_fields: ClassVar[frozenset[str]] = frozenset()

    date_created_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), exclude=True)
    embedding: list[float] | None = Field(default=None, exclude=True)
    actors: list[BaseActor] = Field(default_factory=list, exclude=True)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls._metadata_fields = frozenset(
            name for name, info in cls.model_fields.items()
            if info.exclude
        )

    def is_completable(self) -> bool:
        return True

    def is_completed(self) -> bool:
        for field_name in self.model_fields:
            if field_name in self._metadata_fields:
                continue
            if self._is_nullable_field(field_name) and getattr(self, field_name) is None:
                return False
        return True

    @classmethod
    def _is_nullable_field(cls, field_name: str) -> bool:
        field_info = cls.model_fields[field_name]
        annotation = field_info.annotation
        origin = get_origin(annotation)
        if origin is Union or origin is UnionType:
            return type(None) in get_args(annotation)
        return False

    @classmethod
    def get_domain_fields(cls) -> dict[str, FieldInfo]:
        return {
            name: info for name, info in cls.model_fields.items()
            if name not in cls._metadata_fields
        }

    def domain_dump(self, **kwargs: Any) -> dict[str, Any]:
        return self.model_dump(exclude=self._metadata_fields, **kwargs)

    def domain_dump_json(self, **kwargs: Any) -> str:
        return self.model_dump_json(exclude=self._metadata_fields, **kwargs)

    @classmethod
    def domain_json_schema(cls, **kwargs: Any) -> dict[str, Any]:
        schema = cls.model_json_schema(**kwargs)
        if "properties" in schema:
            for field_name in cls._metadata_fields:
                schema["properties"].pop(field_name, None)
        if "required" in schema:
            schema["required"] = [
                f for f in schema["required"] if f not in cls._metadata_fields
            ]
        return schema

    def update_fields(self, diffs: list[FieldDiff]) -> 'BaseStateEntity':
        update_dict = {diff.field_name: diff.new_value for diff in diffs}
        for key, value in update_dict.items():
            setattr(self, key, value)
        return self

    def _add_actor(self, actor: BaseActor | None) -> None:
        if actor is None:
            return
        if not any(existing.id == actor.id for existing in self.actors):
            self.actors.append(actor)

    @classmethod
    def merge(
        cls,
        current: 'BaseStateEntity' | None,
        state_diff: StateDiff,
        on_validation_error: ValidationErrorHandlingMode = ValidationErrorHandlingMode.skip_merge
    ) -> tuple['BaseStateEntity', StateDiff]:
        validation_errors = current.validate_before_merge(state_diff) if current else []

        if validation_errors:
            diff_with_errors = state_diff.model_copy(update={"validation_errors": validation_errors})
            match on_validation_error:
                case ValidationErrorHandlingMode.raise_exception:
                    raise EntityMergeValidationError(
                        f"Can't merge entity {current} with state_diff {state_diff} "
                        f"due to validation errors: {validation_errors}"
                    )
                case ValidationErrorHandlingMode.skip_merge:
                    return current, diff_with_errors.model_copy(update={"diffs": []})

        if current:
            current.update_fields(state_diff.diffs)
            current._add_actor(state_diff.actor)
            return current, state_diff

        update_dict = {diff.field_name: diff.new_value for diff in state_diff.diffs}
        new_entity = cls(**update_dict)
        new_entity._add_actor(state_diff.actor)
        return new_entity, state_diff

    def validate_before_merge(self, state_diff: StateDiff) -> list[str]:
        return []
