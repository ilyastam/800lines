from typing import TypeVar, Generic, Any
import json

from pydantic import BaseModel, Field
from pydantic_core import PydanticUndefined

ContextRef = TypeVar("ContextRef")


class FieldChange(BaseModel):
    field_name: str
    from_value: str
    to_value: str


class StateChange(BaseModel, Generic[ContextRef]):
    context_ref: ContextRef
    changes: list[FieldChange] = Field(default_factory=list)
    validation_errors: list[str] = Field(default_factory=list)

    def clear_changes(self) -> "StateChange[ContextRef]":
        return self.model_copy(update={"changes": []})


def _serialize_value(value: Any) -> str:
    """
    Serialize a value to a string representation for comparison.

    Args:
        value: The value to serialize

    Returns:
        String representation of the value
    """
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, BaseModel):
        return json.dumps(value.model_dump(mode='json'), sort_keys=True)
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def _is_default_value(entity: BaseModel, field_name: str, value: Any) -> bool:
    field_info = type(entity).model_fields.get(field_name)
    if not field_info:
        return False
    if field_info.default is not PydanticUndefined:
        return value == field_info.default
    if field_info.default_factory:
        return value == field_info.default_factory()
    return False


def _compare_field_values(field_name: str, old_value: Any, new_value: Any, prefix: str = "") -> list[FieldChange]:
    """
    Compare two field values and generate FieldChange objects.
    Supports nested models with dot notation.

    Args:
        field_name: Name of the field being compared
        old_value: Previous value
        new_value: New value
        prefix: Prefix for nested field names (used in recursion)

    Returns:
        List of FieldChange objects (empty if values are the same)
    """
    full_field_name = f"{prefix}.{field_name}" if prefix else field_name

    if isinstance(new_value, BaseModel):
        changes = []
        all_fields = set(type(new_value).model_fields.keys())

        if isinstance(old_value, BaseModel):
            all_fields.update(type(old_value).model_fields.keys())

        for nested_field in all_fields:
            old_nested = getattr(old_value, nested_field, None) if old_value else None
            new_nested = getattr(new_value, nested_field, None)
            if not _is_default_value(new_value, nested_field, new_nested):
                changes.extend(_compare_field_values(nested_field, old_nested, new_nested, full_field_name))

        return changes

    old_str = _serialize_value(old_value)
    new_str = _serialize_value(new_value)

    if old_str != new_str:
        return [FieldChange(field_name=full_field_name, from_value=old_str, to_value=new_str)]

    return []
