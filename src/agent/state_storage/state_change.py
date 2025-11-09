from typing import TypeVar, Generic, Any
import json

from pydantic import BaseModel, Field

ContextRef = TypeVar("ContextRef")


class FieldChange(BaseModel):
    field_name: str
    from_value: str
    to_value: str


class StateChange(BaseModel, Generic[ContextRef]):
    context_ref: ContextRef
    changes: list[FieldChange] = Field(default_factory=list)


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

    # If new value is a BaseModel, recurse into it (even if old is None)
    if isinstance(new_value, BaseModel):
        changes = []
        # Get all fields from the new model
        all_fields = set(type(new_value).model_fields.keys())

        # If old value is also a BaseModel, get its fields too
        if isinstance(old_value, BaseModel):
            all_fields.update(type(old_value).model_fields.keys())

        for nested_field in all_fields:
            old_nested = getattr(old_value, nested_field, None) if old_value else None
            new_nested = getattr(new_value, nested_field, None)
            changes.extend(_compare_field_values(nested_field, old_nested, new_nested, full_field_name))

        return changes

    # Compare serialized values
    old_str = _serialize_value(old_value)
    new_str = _serialize_value(new_value)

    if old_str != new_str:
        return [FieldChange(field_name=full_field_name, from_value=old_str, to_value=new_str)]

    return []


def compare_entities(old_entity: BaseModel | None, new_entity: BaseModel, context_ref: Any) -> StateChange | None:
    """
    Compare two entities and generate a StateChange object.

    Args:
        old_entity: Previous version of the entity (None if new)
        new_entity: New version of the entity
        context_ref: Context reference (typically the entity class or identifier)

    Returns:
        StateChange object if there are changes, None otherwise
    """
    changes: list[FieldChange] = []

    # Get fields to compare (exclude fields marked with exclude=True)
    def get_comparable_fields(entity: BaseModel) -> set[str]:
        """Get field names that should be compared (exclude=True fields are skipped)."""
        comparable = set()
        for field_name, field_info in type(entity).model_fields.items():
            # Skip fields marked with exclude=True
            if not field_info.exclude:
                comparable.add(field_name)
        return comparable

    if old_entity is None:
        # New entity - all comparable fields are changes from empty
        for field_name in get_comparable_fields(new_entity):
            new_value = getattr(new_entity, field_name)
            changes.extend(_compare_field_values(field_name, None, new_value))
    else:
        # Compare existing entity - check each comparable field
        all_fields = get_comparable_fields(new_entity)
        if old_entity:
            all_fields.update(get_comparable_fields(old_entity))

        for field_name in all_fields:
            old_value = getattr(old_entity, field_name, None)
            new_value = getattr(new_entity, field_name, None)
            changes.extend(_compare_field_values(field_name, old_value, new_value))

    # Only return StateChange if there are actual changes
    if changes:
        return StateChange(context_ref=context_ref, changes=changes)

    return None