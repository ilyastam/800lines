from agent.inputs import BaseInput
from agent.llm_parser import parse_state_models_with_llm
from agent.state_entity import BaseStateEntity, LlmParsedStateEntity
from agent.state_storage import (
    DefaultEmbeddingService,
    EmbeddingService,
    InMemoryStateStorage,
    StateStorage,
)
from agent.types import StateChange


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
        return all([entity.is_completable() for entity in self.storage.get_all()])

    def is_state_completed(self):
        return all([entity.is_completed() for entity in self.storage.get_all()])

    def compute_state(self, input: BaseInput) -> list[StateChange]:
        """
        Compute and store state from input.

        Args:
            input: The input to process
        """
        input_fields_to_state_models: dict[str, list[type[BaseStateEntity]]] = (
            input.get_extracts_mapping()
        )

        all_parsed_models: list[BaseStateEntity] = []

        for input_field_name, state_model_classes in input_fields_to_state_models.items():
            input_field_value = getattr(input, input_field_name)

            if not input_field_value:
                continue

            llp_parseable_models: list[type[LlmParsedStateEntity]] = list(filter(
                lambda model_class: issubclass(model_class, LlmParsedStateEntity),
                state_model_classes
            ))

            parsed_models = parse_state_models_with_llm(
                input_field_value,
                llp_parseable_models
            )
            if parsed_models:
                all_parsed_models.extend(parsed_models)

        # Store all parsed models
        return self.update_state(all_parsed_models)

    def update_state(self, state_models: list[BaseStateEntity]) -> list[StateChange]:
        """
        Store state models in storage.
        The storage will increment the state version and assign it to all entities.

        Args:
            state_models: List of state entities to store

        Returns:
            List of StateChange objects representing changes made
        """
        state_changes = self.storage.add_entities(state_models)
        return state_changes

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