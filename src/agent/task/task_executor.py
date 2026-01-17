from __future__ import annotations

from abc import ABC, abstractmethod

from agent.task.base_task import BaseTask


class BaseTaskExecutor(ABC):
    @abstractmethod
    def execute(self, task: BaseTask) -> str:
        """Execute a task and return result string."""
        pass
