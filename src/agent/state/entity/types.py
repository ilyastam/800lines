from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field

Primitive = str | int | float | bool | datetime | None


class FieldDiff(BaseModel):
    field_name: str = Field(description="Name of the field to modify")
    new_value: Primitive | list[Primitive] | dict[str, Primitive] = Field(description="New value for the field")
