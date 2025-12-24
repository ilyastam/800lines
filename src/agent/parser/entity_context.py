from __future__ import annotations

from typing import Any
from pydantic import BaseModel, field_serializer

from agent.state.entity.state_entity import BaseStateEntity


class EntityContext(BaseModel):
    """
    Data that represents user intent and that can be changed
    upon user's request.
    """
    entity_class: type[BaseStateEntity]
    entity_schema: dict[str, Any] | None = None
    entity_refs: list[str] | None = None

    @field_serializer('entity_class')
    def serialize_entity_class(self, v: type[BaseStateEntity]) -> str:
        return v.__name__
