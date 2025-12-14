import json

from agent.inputs import BaseInput
from agent.llm_parser import parse_mutation_intent_with_llm
from agent.state_entity import BaseStateEntity
from agent.state_storage import (
    DefaultEmbeddingService,
    EmbeddingService,
    InMemoryStateStorage,
    StateStorage,
)
from agent.types import FieldDiff, ModelContext, MutationIntent


class BaseStateController:
    def __init__(
        self,
        storage: StateStorage | None = None,
        embedding_service: EmbeddingService | None = None
    ):
        """
        Initialize the state controller.

        Args:
            storage: Storage backend to use (defaults to InMemoryStateStorage)
            embedding_service: Embedding service to use (defaults to DefaultEmbeddingService)
        """
        self.embedding_service = embedding_service or DefaultEmbeddingService()
        self.storage = storage or InMemoryStateStorage(
            embedding_service=self.embedding_service
        )

    def is_state_completable(self):
        entities = self.storage.get_all()
        return bool(entities) and all(entity.is_completable() for entity in entities)

    def is_state_completed(self):
        entities = self.storage.get_all()
        return bool(entities) and all(entity.is_completed() for entity in entities)

    def compute_state(self, input: BaseInput) -> list[MutationIntent]:
        """
        Compute and store state from input.

        Args:
            input: The input to process

        Returns:
            List of MutationIntent objects representing changes made
        """
        input_fields_to_state_models = input.get_extracts_mapping()

        all_intents: list[MutationIntent] = []

        for input_field_name, state_model_classes in input_fields_to_state_models.items():
            input_field_value = getattr(input, input_field_name)
            if not input_field_value:
                continue

            model_contexts = [
                ModelContext(model_class=json.dumps(cls.model_json_schema()))
                for cls in state_model_classes
            ]

            intents = parse_mutation_intent_with_llm(
                input_field_value,
                model_contexts,
                prior_interactions=input.context
            )
            all_intents.extend(intents)

        return self.storage.add_intents(all_intents)

    def update_state(self, state_models: list[BaseStateEntity]) -> list[MutationIntent]:
        """
        Store state models in storage.
        Converts entities to MutationIntents and applies them.

        Args:
            state_models: List of state entities to store

        Returns:
            List of MutationIntent objects representing changes made
        """
        intents = self._entities_to_intents(state_models)
        return self.storage.add_intents(intents)

    def _entities_to_intents(self, entities: list[BaseStateEntity]) -> list[MutationIntent]:
        """Convert entities to MutationIntents."""
        intents: list[MutationIntent] = []
        for entity in entities:
            content_dict = entity.content.model_dump(exclude_unset=True, exclude_defaults=True)
            diffs = [FieldDiff(field_name=k, new_value=v) for k, v in content_dict.items()]
            intent = MutationIntent(
                model_class_name=type(entity).__name__,
                diffs=diffs
            )
            intents.append(intent)
        return intents

    def find_related(
        self,
        entity: BaseStateEntity,
        threshold: float = 0.8,
        limit: int = 10,
        order_by: str = "similarity"
    ) -> list[tuple[BaseStateEntity, float]]:
        """
        Find entities related to the given entity.

        Args:
            entity: The entity to find similar entities for
            threshold: Minimum similarity score (0-1)
            limit: Maximum number of results to return
            order_by: How to order results - "similarity" (default) or "chronological"

        Returns:
            List of (entity, similarity_score) tuples
        """
        return self.storage.get_similar(entity, threshold, limit, order_by)

    def get_chronological(
        self,
        start_index: int = 0,
        limit: int | None = None
    ) -> list[BaseStateEntity]:
        """
        Get entities in chronological order.

        Args:
            start_index: Starting index (0-based)
            limit: Maximum number of entities to return (None = all)

        Returns:
            List of entities in chronological order
        """
        return self.storage.get_chronological_range(start_index, limit)