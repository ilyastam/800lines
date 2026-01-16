from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field

Primitive = str | int | float | bool | datetime | None
JsonPrimitive = str | int | float | bool | None


class FieldDiff(BaseModel):
    field_name: str = Field(description="Field name or dot-notation path (e.g., 'location.city')")
    new_value: JsonPrimitive | list[JsonPrimitive] | dict[str, JsonPrimitive] = Field(description="New value for the field")
