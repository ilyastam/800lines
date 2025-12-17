import json

from agent.inputs import BaseInput
from agent.parser.llm_parser import parse_mutation_intent_with_llm
from agent.state.entity.state_entity import BaseStateEntity
from agent.state import BaseStateStorage
from agent.state.entity.types import FieldDiff, EntityContext, MutationIntent


class BaseStateController:
    def __init__(
        self,
        storage: BaseStateStorage | None = None
    ):
        """
        Initialize the state controller.

        Args:
            storage: Storage backend to use (defaults to InMemoryStateStorage)
            embedding_service: Embedding service to use (defaults to DefaultEmbeddingService)
        """
        self.storage = storage

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
                EntityContext(entity_class_name=json.dumps(cls.model_json_schema()))
                for cls in state_model_classes
            ]

            intents = parse_mutation_intent_with_llm(
                input_field_value,
                model_contexts,
                prior_interactions=input.context
            )
            all_intents.extend(intents)

        return self.storage.apply_mutation_intents(all_intents)

    def _entities_to_intents(self, entities: list[BaseStateEntity]) -> list[MutationIntent]:
        intents: list[MutationIntent] = []
        for entity in entities:
            content_dict = entity.content.model_dump(exclude_unset=True, exclude_defaults=True)
            diffs = [FieldDiff(field_name=k, new_value=v) for k, v in content_dict.items()]
            intent = MutationIntent(
                entity_class_name=type(entity).__name__,
                diffs=diffs
            )
            intents.append(intent)
        return intents

