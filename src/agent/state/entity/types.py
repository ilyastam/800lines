from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

Primitive = str | int | float | bool | datetime | None


class FieldDiff(BaseModel):
    field_name: str = Field(description="Field name or dot-notation path (e.g., 'location.city')")
    new_value: Any = Field(description="New value for the field")
