from abc import ABC, abstractmethod
from typing import Iterable

from agent.interaction.base_input import BaseInput
from agent.interaction.base_output import BaseOutput
from agent.interaction.channel.channel import BaseChannel
from agent.state.entity.state_entity import BaseStateEntity
from agent.state.entity.types import MutationIntent


class BaseOutputsController(ABC):

    def __init__(self, output_channel: BaseChannel):
        self.output_channel = output_channel

    @abstractmethod
    def get_state_controller(self):
        pass

    @abstractmethod
    def generate_outputs(self, intents: list[MutationIntent]) -> list[BaseOutput]:
        pass

    @abstractmethod
    def generate_output(self, entity: BaseStateEntity, intent: MutationIntent | None) -> BaseOutput:
        pass

    def emit_relevant_outputs(self, outputs: list[BaseOutput]):
        for output in outputs:
            output_channel = output.get_channel()
            if not output_channel or output_channel != self.output_channel:
                continue

            self.emit_output(output)

    @abstractmethod
    def emit_output(self, output: BaseOutput):
        pass
