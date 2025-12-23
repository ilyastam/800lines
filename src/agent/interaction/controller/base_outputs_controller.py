from abc import ABC, abstractmethod
from typing import Iterable

from agent.interaction.base_input import BaseInput
from agent.interaction.base_output import BaseOutput
from agent.interaction.channel.channel import BaseChannel
from agent.state.entity.state_entity import BaseStateEntity
from agent.state.entity.types import MutationIntent


class BaseOutputsController(ABC):

    def __init__(self, output_channel: BaseChannel, output_types: Iterable[type[BaseOutput]] | None = None):
        self.output_channel = output_channel
        self.output_types: set[type[BaseOutput]] | None = set(output_types) if output_types is not None else None

    @abstractmethod
    def get_state_controller(self):
        pass

    @abstractmethod
    def generate_outputs(self, intents: list[MutationIntent]) -> list[BaseOutput]:
        pass

    @abstractmethod
    def generate_output(self, entity: BaseStateEntity, intent: MutationIntent | None) -> BaseOutput:
        pass

    def emit_relevant(self, outputs: list[BaseOutput]):
        for output in outputs:
            if self.output_types is not None and output.__class__ not in self.output_types:
                continue

            output_channel = output.get_channel()
            if output_channel is not None and output_channel != self.output_channel:
                continue

            self.emit(output)

    @abstractmethod
    def emit(self, output: BaseOutput):
        pass
