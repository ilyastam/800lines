from abc import ABC, abstractmethod
from typing import Any

from agent.state.entity.types import EntityContext, MutationIntent
from agent.state.entity.state_entity import BaseStateEntity


class BaseParser(ABC):
    def __init__(
        self,
        entity_classes: list[type[BaseStateEntity]],
        channel_domains: list[str | None],
    ):
        if not entity_classes:
            raise ValueError("BaseParser requires at least one entity class to target")

        self.entity_classes = entity_classes
        self.channel_domains = channel_domains or [None]

    @abstractmethod
    def parse_mutation_intent(
        self,
        input_text: str,
        entity_contexts: list[EntityContext],
        intent_context: Any | None = None
    ) -> list[MutationIntent]:
        pass
