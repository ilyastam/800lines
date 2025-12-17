from __future__ import annotations

from typing import Any

from agent.state.entity.state_entity import BaseStateEntity, ContentType


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
