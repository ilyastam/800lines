from typing import Any

from agent.types import StateChange, _compare_field_values
from agent.state_entity import BaseStateEntity


def compare_entities(old_entity: BaseStateEntity | None, new_entity: BaseStateEntity, context_ref: Any) -> StateChange | None:
    """
    Compare content fields of two entities and generate a StateChange object.

    Args:
        old_entity: Previous version of the entity (None if new)
        new_entity: New version of the entity
        context_ref: Context reference (typically the entity class or identifier)

    Returns:
        StateChange object if there are changes, None otherwise
    """
    old_content = old_entity.content if old_entity else None
    new_content = new_entity.content

    changes = _compare_field_values("content", old_content, new_content)

    if changes:
        return StateChange(
            context_ref=context_ref,
            changes=changes,
            validation_errors=old_entity.validate_before_merge(new_entity) if old_entity else []
        )
    return None
