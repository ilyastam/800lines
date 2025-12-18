from abc import ABC, abstractmethod

from agent.state.entity.types import EntityContext, MutationIntent


class BaseParser(ABC):
    @abstractmethod
    def parse_mutation_intent(
        self,
        input_text: str,
        entity_contexts: list[EntityContext],
        prior_interactions: list[dict[str, str]] | None = None
    ) -> list[MutationIntent]:
        pass
