import json
import shutil
import textwrap

from agent.interaction.channel.channel import BaseChannel
from agent.interaction.output.llm_output import ChatOutput
from agent.interaction.output.controller.base_outputs_controller import BaseOutputsController
from agent.state.controller.base_state_controller import BaseStateController
from agent.state.entity.state_entity import BaseStateEntity
from agent.parser.mutation_intent import MutationIntent
from openai import OpenAI


class LlmChatOutputsController(BaseOutputsController):

    def __init__(
        self,
        state_controller: BaseStateController,
        client: OpenAI | None = None,
        output_channel: BaseChannel | None = None,
        wrap_width: int | None = None,
    ):
        self.state_controller: BaseStateController = state_controller
        self.outputs: list[ChatOutput] = []
        self.client: OpenAI = client or OpenAI()
        self.wrap_width = wrap_width

        if output_channel is None:
            raise ValueError("An output channel must be provided to initialize the controller")

        super().__init__(output_channel=output_channel)

    def get_state_controller(self):
        return self.state_controller

    def generate_outputs(self, intents: list[MutationIntent]) -> list[ChatOutput]:
        entities: list[BaseStateEntity] = self.get_state_controller().storage.get_all()

        incomplete_entities = [
            entity for entity in entities
            if entity.is_completable() and not entity.is_completed()
        ]

        if not incomplete_entities:
            return []

        intents_by_class: dict[type, MutationIntent] = {intent.entity_class: intent for intent in intents}

        outputs = []
        for entity in incomplete_entities:
            intent: MutationIntent = intents_by_class.get(entity.__class__)
            output = self.generate_output(entity, intent)
            outputs.append(output)

        return outputs

    def generate_output(self, entity: BaseStateEntity, intent: MutationIntent | None) -> ChatOutput:
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
        response would allow us to fill in as many unfilled fields as possible in the following entity:
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
            messages=[{"role": "system", "content": prompt}] + [i.to_llm_message() for i in self.outputs]
        )

        content = completion.choices[0].message.content
        return self.output_channel.create_output(content=content)

    def emit_output(self, output: ChatOutput) -> ChatOutput:
        width = self.wrap_width or max(int(shutil.get_terminal_size().columns * 0.8), 20)
        role = output.get_role()
        role_prefix = f"{role.title()}: " if role else ""
        message = f"{role_prefix}{output.input_value}"
        print(textwrap.fill(message, width=width))
        return output
