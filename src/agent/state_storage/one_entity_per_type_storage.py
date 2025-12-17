import importlib
import json

from agent.state_entity import BaseStateEntity
from agent.state_storage import BaseStateStorage
from agent.types import MutationIntent


def _get_qualified_name(cls: type) -> str:
    return f"{cls.__module__}.{cls.__qualname__}"


class OneEntityPerTypeStorage(BaseStateStorage):

    def __init__(self, entity_classes: list[type[BaseStateEntity]]):
        super().__init__()
        self.store: dict[type[BaseStateEntity], BaseStateEntity | None] = {}
        self._entity_class_name_to_type: dict[str, type[BaseStateEntity]] = {}

        for entity_class in entity_classes:
            if entity_class.__name__ in self._entity_class_name_to_type and self._entity_class_name_to_type[entity_class.__name__] != entity_class:
                raise ValueError(f"{entity_class} collides with {self._entity_class_name_to_type[entity_class.__name__]}")
            self._entity_class_name_to_type[entity_class.__name__] = entity_class

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

    def to_json(self) -> str:
        data = {
            "version": self.version,
            "entity_classes": [
                _get_qualified_name(entity_class)
                for entity_class in self._entity_class_name_to_type.values()
            ],
            "entities": {
                _get_qualified_name(entity_class): self.store.get(entity_class).model_dump(mode='json') if self.store.get(entity_class) else None
                for entity_class in self._entity_class_name_to_type.values()
            }
        }
        return json.dumps(data)

    @classmethod
    def from_json(cls, data: str) -> 'OneEntityPerTypeStorage':
        parsed = json.loads(data)

        entity_classes = []
        for qualified_name in parsed.get("entity_classes", []):
            module_path, class_name = qualified_name.rsplit(".", 1)
            module = importlib.import_module(module_path)
            entity_classes.append(getattr(module, class_name))

        storage = cls(entity_classes)
        storage.version = parsed.get("version", 0)

        for qualified_name, entity_data in parsed.get("entities", {}).items():
            if entity_data is None:
                continue
            module_path, class_name = qualified_name.rsplit(".", 1)
            entity_class = storage._entity_class_name_to_type.get(class_name)
            if entity_class:
                storage.store[entity_class] = entity_class.model_validate(entity_data)

        return storage

