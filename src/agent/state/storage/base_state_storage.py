"""Abstract base class for state storage implementations."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from agent.state.entity.state_entity import BaseStateEntity

if TYPE_CHECKING:
    from agent.parser.mutation_intent import MutationIntent


class BaseStateStorage(ABC):
    """Abstract base class for state storage implementations."""

    def __init__(self):
        self.version = 0

    def get_entity_refs_for_class(self, entity_class: type[BaseStateEntity]) -> list[str] | None:
        return None

    @abstractmethod
    def apply_mutation_intents(self, intents: list[MutationIntent]) -> list[MutationIntent]:
        """
        Apply mutation intents to storage.

        Args:
            intents: List of mutation intents to apply

        Returns:
            List of applied MutationIntent objects
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
