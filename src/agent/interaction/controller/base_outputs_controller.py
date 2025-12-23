from abc import ABC, abstractmethod

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
