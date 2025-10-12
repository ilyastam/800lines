from datetime import datetime, timezone
from typing import ClassVar, Generic, TypeVar
from pydantic import BaseModel, Field

ContentType = TypeVar("ContentType")
CntxType = TypeVar("CntxType")


class DefaultStateEntityContext(BaseModel):
     definition: ClassVar[str] = """
    Captures context of the entity in the form of JSON object: 
    {{
        "authors": json array of names of people who have participated in discussion around the entity, if none can be determined - set empyu array []
        "reason_summary": string - summary of discussion around the entity. null if no discussion avaiable.
    }}    
    """

     authors: list[str] = Field(default_factory=list)
     reason_summary: str | None


class BaseStateEntity(BaseModel, Generic[ContentType, CntxType]):
     content: ContentType
     context: CntxType

class LlmParsedStateEntity(BaseModel, Generic[ContentType, CntxType]):
    definition: ClassVar[str]
    date_created_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    embedding: list[float] | None = None

    @classmethod
    def describe(cls):
        return cls.definition
    
    def __init_subclass__(cls, **kwargs):
            super().__init_subclass__(**kwargs)
            if not hasattr(cls, "definition") or cls.definition is None:
                raise TypeError(f"{cls.__name__} must define a class-level 'definition' attribute")    



