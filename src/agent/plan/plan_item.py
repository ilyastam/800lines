from enum import Enum

from pydantic import BaseModel, Field


class PlanItemType(str, Enum):
    TASK = "task"
    STATE_CHANGE = "state_change"


class PlanItem(BaseModel):
    type: PlanItemType
    content: str = Field(description="Task description or state change summary")
    result: str | None = Field(default=None)
