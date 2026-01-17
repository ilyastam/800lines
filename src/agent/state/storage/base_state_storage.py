"""Abstract base class for state storage implementations."""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from agent.state.entity.state_entity import BaseStateEntity

if TYPE_CHECKING:
    from agent.parser.state_diff import StateDiff
    from agent.task.base_task import BaseTask, TaskStatus


class BaseStateStorage(ABC):
    """Abstract base class for state storage implementations."""

    def __init__(self):
        self.version = 0
        self._tasks: list[BaseTask] = []

    def get_entity_refs_for_class(self, entity_class: type[BaseStateEntity]) -> list[str] | None:
        return None

    @abstractmethod
    def apply_state_diffs(self, state_diffs: list[StateDiff]) -> list[StateDiff]:
        """
        Apply state diffs to storage.

        Args:
            state_diffs: List of state diffs to apply

        Returns:
            List of applied StateDiff objects
        """
        pass

    def get_current_version(self) -> int:
        return self.version

    def increment_version(self) -> int:
        self.version += 1
        return self.version

    @abstractmethod
    def get_all(self, chronological: bool = True) -> list[BaseStateEntity]:
        """
        Get all stored entities.

        Args:
            chronological: If True, return entities in chronological order (oldest first)
                          If False, no specific order guaranteed

        Returns:
            List of all entities
        """
        pass

    @abstractmethod
    def to_json(self) -> str:
        """
        Serialize storage to JSON string.
        Must preserve insertion order when deserialized.

        Returns:
            str
        """
        pass

    @classmethod
    @abstractmethod
    def from_json(cls, data: str) -> 'BaseStateStorage':
        """
        Deserialize storage from JSON str.
        Preserves insertion order from serialization.

        Args:
            data: str

        Returns:
            Reconstructed StateStorage instance
        """
        pass

    def add_tasks(self, tasks: list[BaseTask]) -> list[BaseTask]:
        """
        Store tasks with current version.

        Args:
            tasks: List of tasks to add

        Returns:
            List of added tasks with assigned IDs and version
        """
        from agent.task.base_task import BaseTask

        added_tasks: list[BaseTask] = []
        for task in tasks:
            task_copy = task.model_copy()
            if task_copy.task_id is None:
                task_copy.task_id = str(uuid.uuid4())
            task_copy.version_added = self.version
            self._tasks.append(task_copy)
            added_tasks.append(task_copy)
        return added_tasks

    def get_tasks_for_version(self, version: int) -> list[BaseTask]:
        """Get all tasks added at a specific version."""
        return [task for task in self._tasks if task.version_added == version]

    def get_pending_tasks(self) -> list[BaseTask]:
        """Get all tasks that have not yet been completed or failed."""
        from agent.task.base_task import TaskStatus

        return [
            task for task in self._tasks
            if task.status in (TaskStatus.NOT_STARTED, TaskStatus.IN_PROGRESS)
        ]

    def update_task(self, task_id: str, status: TaskStatus, result: str | None = None) -> BaseTask | None:
        """
        Update a task's status and optionally its result.

        Args:
            task_id: ID of the task to update
            status: New status
            result: Optional result to set

        Returns:
            Updated task if found, None otherwise
        """
        for task in self._tasks:
            if task.task_id == task_id:
                task.status = status
                if result is not None:
                    task.result = result
                return task
        return None

    def get_all_tasks(self) -> list[BaseTask]:
        """Get all tasks."""
        return list(self._tasks)
