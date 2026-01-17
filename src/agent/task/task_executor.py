from __future__ import annotations

from abc import ABC, abstractmethod

from agent.task.base_task import BaseTask, TaskResult


class BaseTaskExecutor(ABC):
    @abstractmethod
    def execute(self, task: BaseTask) -> TaskResult:
        """
        Execute a task and return result with any state diffs produced.

        The executor (e.g., LLM with tools) processes the task and returns:
        - Updated task with result and status
        - Any state diffs that should be applied based on task result
        """
        pass

    def execute_all(self, tasks: list[BaseTask]) -> list[TaskResult]:
        """Execute all tasks and return results."""
        return [self.execute(task) for task in tasks]
