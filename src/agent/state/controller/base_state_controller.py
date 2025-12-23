from agent.interaction.base_input import BaseInput
from agent.interaction.base_output import BaseOutput
from agent.interaction.channel.channel import BaseChannel
from agent.interaction.interaction import Interaction
from agent.parser import BaseParser, get_parser_for_entity
from agent.state.entity.state_entity import BaseStateEntity
from agent.state import BaseStateStorage
from agent.state.entity.types import FieldDiff, EntityContext, MutationIntent


class BaseStateController:
    def __init__(
        self,
        storage: BaseStateStorage | None = None,
    ):
        """
        Initialize the state controller.

        Args:
            storage: Storage backend to use
        """
        self.storage = storage
        self.interactions: list[Interaction] = []

    def is_state_completable(self):
        entities = self.storage.get_all()
        return bool(entities) and all(entity.is_completable() for entity in entities)

    def is_state_completed(self):
        entities = self.storage.get_all()
        return bool(entities) and all(entity.is_completed() for entity in entities)

    def parse_mutation_intents(self, inputs: list[BaseInput]) -> list[MutationIntent]:
        all_intents: list[MutationIntent] = []

        for _input in inputs:
            if not _input.input_value:
                continue

            state_entity_classes = list(_input.extracts_to)
            classes_by_parser: dict[BaseParser, list[type[BaseStateEntity]]] = {}
            for cls in state_entity_classes:
                parser = self._get_parser_for_entity_and_channel(cls, _input.channel)
                if parser is None:
                    raise ValueError(f"No parser registered for entity class {cls.__name__}")
                if parser not in classes_by_parser:
                    classes_by_parser[parser] = []
                classes_by_parser[parser].append(cls)

            for parser, classes in classes_by_parser.items():
                entity_contexts = [
                    EntityContext(
                        entity_class=cls,
                        entity_schema=cls.model_json_schema(),
                        entity_refs=self.storage.get_entity_refs_for_class(cls)
                    ) for cls in classes
                ]
                intents = parser.parse_mutation_intent(
                    _input.input_value,
                    entity_contexts,
                    prior_interactions=self.get_interactions()
                )
                for intent in intents:
                    intent.actor = _input.actor
                all_intents.extend(intents)

        return all_intents

    def record_input(self, input_obj: BaseInput):
        self.interactions.append(input_obj)

    def record_output(self, output_obj: BaseOutput):
        self.interactions.append(output_obj)

    def get_interactions(self) -> list[Interaction]:
        return self.interactions

    def _get_parser_for_entity_and_channel(
        self, entity_cls: type[BaseStateEntity], channel: BaseChannel
    ) -> BaseParser | None:
        return get_parser_for_entity(entity_cls, channel.channel_domain)

    @staticmethod
    def _entities_to_intents(entities: list[BaseStateEntity]) -> list[MutationIntent]:
        intents: list[MutationIntent] = []
        for entity in entities:
            content_dict = entity.content.model_dump(exclude_unset=True, exclude_defaults=True)
            diffs = [FieldDiff(field_name=k, new_value=v) for k, v in content_dict.items()]
            intent = MutationIntent(
                entity_class=type(entity),
                diffs=diffs
            )
            intents.append(intent)
        return intents

    def update_state(self, inputs: list[BaseInput]) -> list[MutationIntent]:
        """
        Compute and store state from input.

        Args:
            inputs: inputs to process

        Returns:
            List of MutationIntent objects representing changes made
        """
        all_intents: list[MutationIntent] = self.parse_mutation_intents(inputs)
        return self.storage.apply_mutation_intents(all_intents)
