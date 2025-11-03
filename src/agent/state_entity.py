from datetime import datetime, timezone
from typing import ClassVar, Generic, TypeVar, Any
from pydantic import BaseModel, Field, model_validator

ContentType = TypeVar("ContentType")
CntxType = TypeVar("CntxType")


class DefaultStateEntityContext(BaseModel):
     definition: ClassVar[str] = """
    Captures context of the entity in the form of JSON object: 
    {{
        "authors": json array of names of people who have participated in discussion around the entity, if none can be determined - set empty array []
        "reason_summary": string - summary of discussion around the entity. null if no discussion avaiable.
    }}    
    """

     authors: list[str] = Field(default_factory=list)
     reason_summary: str | None


class BaseStateEntity(BaseModel, Generic[ContentType, CntxType]):
     content: ContentType
     context: CntxType

class LlmParsedStateEntity(BaseModel, Generic[ContentType]):
    definition: ClassVar[str]
    date_created_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), json_schema_extra={"exclude": True})
    embedding: list[float] | None = Field(default=None, exclude=True)
    

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

    @classmethod
    def describe(cls):
        return cls.definition
    
    def __init_subclass__(cls, **kwargs):
            super().__init_subclass__(**kwargs)
            # Skip the check for Pydantic's internally generated generic submodels
            # These are created when using Generic[T] syntax and have special names
            if hasattr(cls, "__pydantic_generic_metadata__") or "LlmParsedStateEntity[" in cls.__name__:
                return
            # Check if 'definition' is actually defined in the subclass's __dict__
            # (not just inherited or annotated without a value)
            if "definition" not in cls.__dict__ or cls.__dict__.get("definition") is None:
                raise TypeError(f"{cls.__name__} must define a class-level 'definition' attribute")



