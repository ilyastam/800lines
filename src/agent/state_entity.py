from datetime import datetime, timezone
from typing import ClassVar, Generic, TypeVar, Any
from pydantic import BaseModel, Field, model_validator

ContentType = TypeVar("ContentType")


class BaseStateEntity(BaseModel, Generic[ContentType]):
    content: ContentType
    date_created_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), json_schema_extra={"exclude": True})
    embedding: list[float] | None = Field(default=None, exclude=True)


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

    



