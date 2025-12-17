from abc import ABC, abstractmethod

from agent.state.entity.state_entity import BaseStateEntity
from agent.state.entity.types import MutationIntent
from openai import OpenAI

client = OpenAI()

class BaseInteractionsController(ABC):

    @abstractmethod
    def get_state_controller(self):
        pass

    @abstractmethod
    def generate_interactions(self, intents: list[MutationIntent]) -> list[str]:
        pass

    @abstractmethod
    def generate_interaction(self, entity: BaseStateEntity, intent: MutationIntent | None) -> str:
        pass

    @abstractmethod
    def record_interaction(self, interaction: str):
        pass
