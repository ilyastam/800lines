from __future__ import annotations

from pydantic import BaseModel, Field


class BaseTask(BaseModel):
    task_id: str | None = Field(default=None)
    task: str = Field(description="description of the task")
    result: str | None = Field(default=None)
    version_added: int = Field(default=0)
