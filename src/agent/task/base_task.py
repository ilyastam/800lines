from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from agent.parser.state_diff import StateDiff


class TaskStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    FAILED = "failed"
    COMPLETED = "completed"


class BaseTask(BaseModel):
    task_id: str | None = Field(default=None)
    task: str = Field(description="description of the task received from the input")
    result: str | None = Field(default=None, description="result of the task")
    status: TaskStatus = Field(default=TaskStatus.NOT_STARTED)
    version_added: int = Field(default=0)


class TaskResult(BaseModel):
    task: BaseTask
    state_diffs: list[StateDiff] = Field(
        default_factory=list,
        description="State diffs produced by this task's execution"
    )

    model_config = {"arbitrary_types_allowed": True}
