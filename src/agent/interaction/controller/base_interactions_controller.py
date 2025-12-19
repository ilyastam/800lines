from abc import ABC, abstractmethod

from agent.interaction.base_interaction import BaseInteraction
from agent.state.entity.state_entity import BaseStateEntity
from agent.state.entity.types import MutationIntent

class BaseInteractionsController(ABC):

    @abstractmethod
    def get_state_controller(self):
        pass

    @abstractmethod
    def generate_interactions(self, intents: list[MutationIntent]) -> list[BaseInteraction]:
        pass

    @abstractmethod
    def generate_interaction(self, entity: BaseStateEntity, intent: MutationIntent | None) -> BaseInteraction:
        pass

    @abstractmethod
    def record_interaction(self, interaction: BaseInteraction):
        pass
