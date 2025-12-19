from abc import ABC, abstractmethod
from typing import Any

from agent.state.entity.types import EntityContext, MutationIntent


class BaseParser(ABC):
    @abstractmethod
    def parse_mutation_intent(
        self,
        input_text: str,
        entity_contexts: list[EntityContext],
        intent_context: Any | None = None
    ) -> list[MutationIntent]:
        pass
