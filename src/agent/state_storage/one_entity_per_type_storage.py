from collections import OrderedDict

from agent.state_entity import BaseStateEntity
from agent.state_storage import BaseStateStorage
from agent.types import MutationIntent


class OneEntityPerTypeStorage(BaseStateStorage):

    def __init__(self, entity_classes: list[type[BaseStateEntity]]):
        super().__init__()
        self.store: dict[type[BaseStateEntity], BaseStateEntity | None] = {}
        self._entity_class_name_to_type: dict[str, type[BaseStateEntity]] = {
            entity_type.__name__: entity_type for entity_type in entity_classes
        }

    def apply_mutation_intents(self, intents: list[MutationIntent]) -> list[MutationIntent]:
        applied_intents: list[MutationIntent] = []

        for intent in intents:
            applied_intent: MutationIntent | None = None
            entity_class: type[BaseStateEntity] = self._entity_class_name_to_type.get(intent.entity_class_name, None)
            if not entity_class:
                continue
            self.store[entity_class], applied_intent = entity_class.merge(
                self.store.get(entity_class),
                intent
            )

            if applied_intent and applied_intent.diffs:
                applied_intents.append(applied_intent)
                self.increment_version()

        return applied_intents

    def get_all(self, chronological: bool = True) -> list[BaseStateEntity]:
        return [
            self.store[entity_class] for entity_class in self._entity_class_name_to_type.values()
            if entity_class in self.store
        ]

    def to_json(self) -> dict:
        pass

    @classmethod
    def from_json(cls, data: dict) -> 'BaseStateStorage':
        pass

