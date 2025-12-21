from abc import ABC, abstractmethod

from agent.interaction.base_interaction import BaseInteraction
from agent.interaction.channel.channel import BaseChannel


class BaseChannelConnector(ABC):

    def __init__(self, interaction_types: set[type[BaseInteraction]], channel: BaseChannel):
        self.interaction_types = interaction_types
        self.channel = channel

    def emit_relevant(self, interactions: list[BaseInteraction]):
        for interaction in interactions:
            if interaction.__class__ in self.interaction_types:
                interaction_channel = interaction.get_channel()
                if interaction_channel is not None and interaction_channel != self.channel:
                    continue
                self.emit(interaction)

    @abstractmethod
    def emit(self, interaction: BaseInteraction):
        pass
