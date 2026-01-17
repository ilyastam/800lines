from __future__ import annotations

from typing import TYPE_CHECKING

from agent.interaction.input.base_input import BaseInput
from agent.interaction.output.base_output import BaseOutput
from agent.interaction.channel.channel import BaseChannel
from agent.interaction.interaction import Interaction
from agent.parser import BaseParser, get_parser_for_entity
from agent.parser.entity_context import EntityContext
from agent.parser.parse_result import ParseResult
from agent.parser.state_diff import StateDiff
from agent.state.entity.state_entity import BaseStateEntity
from agent.state import BaseStateStorage
from agent.state.entity.types import FieldDiff
from agent.task.base_task import BaseTask

if TYPE_CHECKING:
    from agent.task.task_parser import TaskParser


class BaseStateController:
    def __init__(
        self,
        storage: BaseStateStorage | None = None,
        task_parser: TaskParser | None = None,
    ):
        """
        Initialize the state controller.

        Args:
            storage: Storage backend to use
            task_parser: Parser for task-only inputs (inputs with empty extracts_to)
        """
        self.storage = storage
        self.task_parser = task_parser
        self.interactions: list[Interaction] = []

    def is_state_completable(self):
        entities = self.storage.get_all()
        return bool(entities) and all(entity.is_completable() for entity in entities)

    def is_state_completed(self):
        entities = self.storage.get_all()
        return bool(entities) and all(entity.is_completed() for entity in entities)

    def parse_inputs(self, inputs: list[BaseInput]) -> ParseResult:
        all_diffs: list[StateDiff] = []
        all_tasks: list[BaseTask] = []

        for _input in inputs:
            if not _input.input_value:
                continue

            state_entity_classes = list(_input.extracts_to)

            if not state_entity_classes:
                if self.task_parser:
                    tasks = self.task_parser.parse_tasks(_input.input_value)
                    all_tasks.extend(tasks)
                continue

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
                parse_result = parser.parse_state_diff(
                    _input.input_value,
                    entity_contexts,
                    prior_interactions=self.get_interactions()
                )
                for diff in parse_result.state_diffs:
                    diff.actor = _input.actor
                all_diffs.extend(parse_result.state_diffs)
                all_tasks.extend(parse_result.tasks)

        return ParseResult(state_diffs=all_diffs, tasks=all_tasks)

    def record_input(self, input_obj: BaseInput):
        self.interactions.append(input_obj)

    def record_outputs(self, outputs: list[BaseOutput]):
        self.interactions.extend(outputs)

    def get_interactions(self) -> list[Interaction]:
        return self.interactions

    def _get_parser_for_entity_and_channel(
        self, entity_cls: type[BaseStateEntity], channel: BaseChannel
    ) -> BaseParser | None:
        return get_parser_for_entity(entity_cls, channel.channel_domain)

    @staticmethod
    def _entities_to_diffs(entities: list[BaseStateEntity]) -> list[StateDiff]:
        state_diffs: list[StateDiff] = []
        for entity in entities:
            content_dict = entity.domain_dump(exclude_unset=True, exclude_defaults=True)
            diffs = [FieldDiff(field_name=k, new_value=v) for k, v in content_dict.items()]
            state_diff = StateDiff(
                entity_class=type(entity),
                diffs=diffs
            )
            state_diffs.append(state_diff)
        return state_diffs

    def update_state(self, inputs: list[BaseInput]) -> tuple[list[StateDiff], list[BaseTask]]:
        """
        Compute and store state from input.

        Args:
            inputs: inputs to process

        Returns:
            Tuple of (applied StateDiffs, tasks parsed from input)
        """
        parse_result: ParseResult = self.parse_inputs(inputs)
        applied_diffs = self.storage.apply_state_diffs(parse_result.state_diffs)
        added_tasks = self.storage.add_tasks(parse_result.tasks)
        return applied_diffs, added_tasks
