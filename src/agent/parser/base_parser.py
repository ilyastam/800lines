from abc import ABC, abstractmethod
from typing import Any

from agent.interaction.interaction import Interaction

from agent.parser.entity_context import EntityContext
from agent.parser.state_diff import StateDiff
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
    def parse_state_diff(
        self,
        input_text: str,
        entity_contexts: list[EntityContext],
        prior_interactions: list[Interaction] | None = None
    ) -> list[StateDiff]:
        pass
