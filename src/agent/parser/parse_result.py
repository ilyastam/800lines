from __future__ import annotations

from pydantic import BaseModel, Field

from agent.parser.state_diff import StateDiff
from agent.task.base_task import BaseTask


class ParseResult(BaseModel):
    """Result of parsing user input containing both state diffs and tasks."""
    state_diffs: list[StateDiff] = Field(default_factory=list)
    tasks: list[BaseTask] = Field(default_factory=list)

    model_config = {"arbitrary_types_allowed": True}
