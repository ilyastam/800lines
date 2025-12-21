from abc import ABC, abstractmethod

from agent.inputs import BaseInput
from agent.interaction.base_interaction import BaseInteraction
from agent.interaction.channel.channel import BaseChannel
from agent.state.entity.state_entity import BaseStateEntity
from agent.state.entity.types import MutationIntent


class BaseInteractionsController(ABC):

    def __init__(self, input_channels: set[BaseChannel], output_channel: BaseChannel):
        self.input_channels = input_channels
        self.output_channel = output_channel

    @abstractmethod
    def get_state_controller(self):
        pass

    @abstractmethod
    def generate_interactions(self, intents: list[MutationIntent]) -> list[BaseInteraction]:
        pass

    @abstractmethod
    def generate_interaction(self, entity: BaseStateEntity, intent: MutationIntent | None) -> BaseInteraction:
        pass

    def record_interaction(self, interaction: BaseInteraction):
        interaction_channel = interaction.get_channel()
        if interaction_channel is None:
            return

        if interaction_channel != self.output_channel and interaction_channel not in self.input_channels:
            return

        self._record_interaction(interaction)

    @abstractmethod
    def _record_interaction(self, interaction: BaseInteraction):
        pass

    @abstractmethod
    def record_input(self, input: BaseInput):
        pass
