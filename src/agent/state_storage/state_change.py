from typing import Any

from pydantic import BaseModel

from agent.types import StateChange, FieldChange, _compare_field_values
from agent.state_entity import BaseStateEntity


def compare_entities(old_entity: BaseStateEntity | None, new_entity: BaseStateEntity, context_ref: Any) -> StateChange | None:
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

    def get_comparable_fields(entity: BaseModel) -> set[str]:
        """Get field names that should be compared (exclude=True fields are skipped)."""
        comparable = set()
        for field_name, field_info in type(entity).model_fields.items():
            if not field_info.exclude:
                comparable.add(field_name)
        return comparable

    if old_entity is None:
        for field_name in get_comparable_fields(new_entity):
            new_value = getattr(new_entity, field_name)
            changes.extend(_compare_field_values(field_name, None, new_value))
    else:
        all_fields = get_comparable_fields(new_entity)
        if old_entity:
            all_fields.update(get_comparable_fields(old_entity))

        for field_name in all_fields:
            old_value = getattr(old_entity, field_name, None)
            new_value = getattr(new_entity, field_name, None)
            changes.extend(_compare_field_values(field_name, old_value, new_value))

    if changes:
        return StateChange(context_ref=context_ref,
                           changes=changes,
                           validation_errors=old_entity.validate_before_merge(new_entity) if old_entity else [])
    return None
