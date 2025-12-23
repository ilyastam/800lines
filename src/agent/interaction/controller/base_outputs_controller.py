from abc import ABC, abstractmethod

from agent.interaction.base_input import BaseInput
from agent.interaction.base_output import BaseOutput
from agent.interaction.channel.channel import BaseChannel
from agent.state.entity.state_entity import BaseStateEntity
from agent.state.entity.types import MutationIntent


class BaseOutputsController(ABC):

    def __init__(self, input_channels: set[BaseChannel], output_channel: BaseChannel):
        self.input_channels = input_channels
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

    def record_output(self, output: BaseOutput):
        output_channel = output.get_channel()
        if output_channel is None:
            return

        if output_channel != self.output_channel and output_channel not in self.input_channels:
            return

        self._record_output(output)

    @abstractmethod
    def _record_output(self, output: BaseOutput):
        pass

    @abstractmethod
    def record_input(self, input: BaseInput):
        pass
