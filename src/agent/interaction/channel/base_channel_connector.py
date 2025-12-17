from abc import ABC, abstractmethod

from agent.interaction.base_interaction import BaseInteraction


class BaseChannelConnector(ABC):

    def __init__(self, interaction_types: set[type[BaseInteraction]]):
        self.interaction_types = interaction_types

    @abstractmethod
    def emit_relevant(self, interactions: list[BaseInteraction]):
        for interaction in interactions:
            if interaction.__class__ in self.interaction_types:
                self.emit(interaction)

    @abstractmethod
    def emit(self, interaction: BaseInteraction):
        pass
