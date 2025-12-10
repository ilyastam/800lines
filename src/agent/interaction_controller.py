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

    def generate_interactions(self, changes: list[StateChange], ) -> list[str]:
        if not changes:
            return []

        for change in changes:
            interaction = self.generate_interaction(change)
            if interaction:
                return [interaction]

        return []

    def generate_interaction(self, change: StateChange) -> str | None:
        entities: list[BaseStateEntity] = self.get_state_controller().storage.get_all()

        target_entity = None
        for entity in entities:
            if entity.__class__.__name__ == change.context_ref:
                target_entity = entity
                break

        if not target_entity:
            return None

        entity_json = target_entity.content.model_dump_json(indent=2, exclude_none=True)
        entity_schema = json.dumps(target_entity.content.model_json_schema(), indent=2)
        change_json = change.model_dump_json(indent=2, exclude_none=True)

        prompt = textwrap.dedent(f"""
        Your task is to generate a message to the user such that their
        response would allow us to fill in all unfilled fields in the following entity:
        {entity_schema}

        So far the following data has been collected:
        {entity_json}

        Last interaction resulted in the following change:
        {change_json}

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
            messages=self.interactions + [{"role": "system", "content": prompt}]
        )

        interaction = completion.choices[0].message.content
        self.record_interaction({'role': 'assistant', 'content': interaction})
        return interaction