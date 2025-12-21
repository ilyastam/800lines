import json
import textwrap

from agent.inputs import BaseInput
from agent.interaction.channel.channel import BaseChannel
from agent.interaction.llm_interaction import ChatInteraction
from agent.interaction.controller.base_interactions_controller import BaseInteractionsController
from agent.state.controller.base_state_controller import BaseStateController
from agent.state.entity.state_entity import BaseStateEntity
from agent.state.entity.types import MutationIntent
from openai import OpenAI


class LlmChatInteractionsController(BaseInteractionsController):

    def __init__(
        self,
        state_controller: BaseStateController,
        client: OpenAI | None = None,
        input_channels: set[BaseChannel] | None = None,
        output_channel: BaseChannel | None = None,
    ):
        self.state_controller: BaseStateController = state_controller
        self.interactions: list[ChatInteraction] = []
        self.client: OpenAI = client or OpenAI()

        if output_channel is None:
            raise ValueError("An output channel must be provided to initialize the controller")

        super().__init__(input_channels=input_channels or set(), output_channel=output_channel)

    def get_state_controller(self):
        return self.state_controller

    def _record_interaction(self, interaction_object: ChatInteraction):
        self.interactions.append(interaction_object)

    def record_input(self, input: BaseInput):
        pass

    def generate_interactions(self, intents: list[MutationIntent]) -> list[ChatInteraction]:
        entities: list[BaseStateEntity] = self.get_state_controller().storage.get_all()

        incomplete_entities = [
            entity for entity in entities
            if entity.is_completable() and not entity.is_completed()
        ]

        if not incomplete_entities:
            return []

        intents_by_class_name = {intent.entity_class_name: intent for intent in intents}

        interactions = []
        for entity in incomplete_entities:
            entity_class_name = entity.__class__.__name__
            intent = intents_by_class_name.get(entity_class_name)
            # TODO: implement limit of interactions per channel
            interaction = self.generate_interaction(entity, intent)
            interactions.append(interaction)

        return interactions

    def generate_interaction(self, entity: BaseStateEntity, intent: MutationIntent | None) -> ChatInteraction:
        entity_json = entity.content.model_dump_json(indent=2, exclude_none=True)
        entity_schema = json.dumps(entity.content.model_json_schema(), indent=2)

        if intent:
            intent_json = intent.model_dump_json(indent=2, exclude_none=True)
            change_context = f"""
        Last interaction resulted in the following change:
        {intent_json}
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

        completion = self.client.chat.completions.parse(
            model="gpt-4o",
            messages=[{"role": "system", "content": prompt}] + [i.to_llm_message() for i in self.interactions]
        )

        content = completion.choices[0].message.content
        return self.output_channel.create_interaction(role='assistant', content=content)
