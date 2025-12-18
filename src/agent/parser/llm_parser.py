from typing import Any, Union
from openai import OpenAI
from pydantic import create_model

from agent.parser.base_parser import BaseParser
from agent.state.entity.llm_parsed_entity import LlmParsedStateEntity
from agent.state.entity.types import EntityContext, MutationIntent, MutationIntents

client = OpenAI()


class LlmParser(BaseParser):
    def parse_mutation_intent(
        self,
        input_text: str,
        entity_contexts: list[EntityContext],
        prior_interactions: list[dict[str, str]] | None = None
    ) -> list[MutationIntent]:
        return parse_mutation_intent_with_llm(input_text, entity_contexts, prior_interactions)


def parse_state_models_with_llm(input_text: str,
                                state_model_classes: list[type[LlmParsedStateEntity]],
                                context: list[dict[str, str]] | None = None
                                ) -> list[Any] | None:
    COMBINED_STATE_MODELS_SCHEMA = create_model(
        "COMBINED_STATE_MODELS_SCHEMA",
        parsed_models=(list[Union[tuple(state_model_classes) + (type(None),)]] | None, None),
    )

    messages = (context or []) + [
        {"role": "system", "content": "Extract the entity from the text. Only include fields that have values different from their default values."},
        {"role": "user", "content": input_text},
    ]

    completion = client.chat.completions.parse(
        model="gpt-4o",
        messages=messages,
        response_format=COMBINED_STATE_MODELS_SCHEMA,
        temperature=0.0
    )

    event = completion.choices[0].message.parsed
    return event.parsed_models if hasattr(event, 'parsed_models') else None


def parse_mutation_intent_with_llm(input_text: str,
                                   entity_context: list[EntityContext],
                                   prior_interactions: list[dict[str, str]] | None = None
                                   ) -> list[MutationIntent]:

    combined_entity_ctx = "\n".join([mctx.model_dump_json() for mctx in entity_context])

    messages = (prior_interactions or []) + [
        {"role": "system", "content": "Below is the description of data entities that user can modify (set or unset a field value). User may also say something unrelated to these entities. If user intends to modify model entities, capture and return their intent according to provided response schema. If the intent is to unset a field - return default value for this field according to schema."},
        {"role": "system", "content": combined_entity_ctx},
        {"role": "user", "content": input_text},
    ]

    completion = client.chat.completions.parse(
        model="gpt-4o",
        messages=messages,
        response_format=MutationIntents,
        temperature=0.0
    )

    event: MutationIntents = completion.choices[0].message.parsed
    return event.intents


def register_llm_parser() -> None:
    from agent.parser.parser_registry import register_parser
    register_parser(LlmParsedStateEntity, LlmParser())

