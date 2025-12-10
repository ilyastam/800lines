import json
import textwrap
from abc import ABC, abstractmethod

from agent.state_controller import BaseStateController
from agent.state_entity import BaseStateEntity
from agent.types import StateChange
from openai import OpenAI

client = OpenAI()

class BaseInteractionsController(ABC):

    @abstractmethod
    def get_state_controller(self):
        pass

    @abstractmethod
    def generate_interactions(self, changes: list[StateChange]) -> list[str]:
        pass

    @abstractmethod
    def generate_interaction(self, entity: BaseStateEntity, change: StateChange | None) -> str:
        pass

    @abstractmethod
    def record_interaction(self, interaction: str):
        pass


class LlmInteractionsController(BaseInteractionsController):

    def __init__(self, state_controller: BaseStateController):
        self.state_controller: BaseStateController = state_controller
        self.interactions: list[dict[str, str]] = []

    def get_state_controller(self):
        return self.state_controller

    def record_interaction(self, interaction_object: dict[str, str]):
        self.interactions.append(interaction_object)

    def generate_interactions(self, changes: list[StateChange]) -> list[str]:
        entities: list[BaseStateEntity] = self.get_state_controller().storage.get_all()

        incomplete_entities = [
            entity for entity in entities
            if entity.is_completable() and not entity.is_completed()
        ]

        if not incomplete_entities:
            return []

        changes_by_context_ref = {change.context_ref: change for change in changes}

        interactions = []
        for entity in incomplete_entities:
            entity_class_name = entity.__class__.__name__
            change = changes_by_context_ref.get(entity_class_name)
            interaction = self.generate_interaction(entity, change)
            interactions.append(interaction)

        return interactions

    def generate_interaction(self, entity: BaseStateEntity, change: StateChange | None) -> str:
        entity_json = entity.content.model_dump_json(indent=2, exclude_none=True)
        entity_schema = json.dumps(entity.content.model_json_schema(), indent=2)

        if change:
            change_json = change.model_dump_json(indent=2, exclude_none=True)
            change_context = f"""
        Last interaction resulted in the following change:
        {change_json}
        """
        else:
            change_context = ""

        prompt = textwrap.dedent(f"""
        Your task is to generate a message to the user such that their
        response would allow us to fill in all unfilled fields in the following entity:
        {entity_schema}

        So far the following data has been collected:
        {entity_json}
        {change_context}
        you are chatting with the person, so strive for balance between casual and professional.
        Make the message sound natural, acknowledge what user said in their last message, maintain the thread, but
        advance the conversation to the objective of filling in all entities with expected valid data.

        Optimize for generating instructions that are first and foremost user-friendly.
        Be brief with thanks.

        It's okay to not ask for all missing data in one message, we can always ask a follow up question.
        Only ask for data that is defined in schemas, and is missing or invalid.

        If user is asking a question related to the data you have - answer it. If user is asking a question about a general topic - answer it, but
        let them know that they need to check facts on their own.
        """)

        print(prompt)

        completion = client.chat.completions.parse(
            model="gpt-4o",
            messages=[{"role": "system", "content": prompt}] + self.interactions
        )

        interaction = completion.choices[0].message.content
        return interaction