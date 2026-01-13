import json
from typing import Any
from openai import OpenAI
from pydantic import BaseModel

from agent.interaction.interaction import Interaction
from agent.parser.base_parser import BaseParser
from agent.state.entity.actor.default_actor import DefaultActor
from agent.state.entity.llm_parsed_entity import LlmParsedStateEntity
from agent.parser.entity_context import EntityContext
from agent.parser.state_diff import StateDiff, LlmStateDiffs


class LlmParser(BaseParser):
    def __init__(
        self,
        client: OpenAI | None = None,
        entity_classes: list[type[LlmParsedStateEntity]] | None = None,
        channel_domains: list[str | None] | None = None,
    ):
        super().__init__(
            entity_classes=entity_classes or [LlmParsedStateEntity],
            channel_domains=channel_domains or [None],
        )
        self.client: OpenAI = client or OpenAI()

    def parse_state_diff(
        self,
        input_text: str,
        entity_contexts: list[EntityContext],
        prior_interactions: list[Interaction | Any] | None = None
    ) -> list[StateDiff]:
        combined_entity_ctx = "\n".join([mctx.model_dump_json() for mctx in entity_contexts])
        _prior_messages: list[dict[str, str]] = self._prepare_prior_messages(prior_interactions)

        messages = _prior_messages + [
            {"role": "system", "content": "Below is the description of data entities that user can modify (set or unset a field value). User may also say something unrelated to these entities. If user intends to modify model entities, capture and return their intent according to provided response schema. If the intent is to unset a field - return default value for this field according to schema."},
            {"role": "system", "content": combined_entity_ctx},
            {"role": "user", "content": input_text},
        ]

        completion = self.client.chat.completions.parse(
            model="gpt-4o",
            messages=messages,
            response_format=LlmStateDiffs,
            temperature=0.0
        )

        llm_response: LlmStateDiffs = completion.choices[0].message.parsed
        entity_class_map = {ctx.entity_class.__name__: ctx.entity_class for ctx in entity_contexts}

        return [
            StateDiff(
                entity_class=entity_class_map[llm_diff.entity_class_name],
                entity_ref=llm_diff.entity_ref,
                diffs=llm_diff.diffs,
            )
            for llm_diff in llm_response.diffs
            if llm_diff.entity_class_name in entity_class_map
        ]

    @staticmethod
    def _prepare_prior_messages(intent_context: list[Interaction | Any] | None = None) -> list[dict[str, str]]:
        _intent_context: list[dict[str, str]] = []
        for entity_context in (intent_context or []):
            if isinstance(entity_context, Interaction):
                to_message = getattr(entity_context, "to_llm_message", None)
                if callable(to_message):
                    _intent_context.append(to_message())
                    continue

                content = getattr(entity_context, "input_value", None)
                if content is None:
                    continue
                if isinstance(content, BaseModel):
                    content = content.model_dump_json()
                elif isinstance(content, (list, dict)):
                    try:
                        content = json.dumps(content)
                    except Exception:
                        content = str(content)
                else:
                    content = str(content)
                role = "assistant" if isinstance(entity_context.actor, DefaultActor) else "user"
                _intent_context.append({"role": role, "content": content})
            elif isinstance(entity_context, BaseModel):
                _intent_context.append({"role": "system", "content": entity_context.model_dump_json()})
            elif isinstance(entity_context, (list, dict)):
                try:
                    _intent_context.append({"role": "system", "content": json.dumps(entity_context)})
                except Exception:
                    pass
            elif entity_context:
                try:
                    _intent_context.append({"role": "system", "content": str(entity_context)})
                except Exception:
                    pass

        return _intent_context


def parse_state_diff_with_llm(input_text: str,
                              entity_contexts: list[EntityContext],
                              context: list[dict[str, str]] | None = None,
                              client: OpenAI | None = None
                              ) -> list[StateDiff]:

    combined_entity_ctx = "\n".join([mctx.model_dump_json() for mctx in entity_contexts])

    messages = (context or []) + [
        {"role": "system", "content": "Below is the description of data entities that user can modify (set or unset a field value). User may also say something unrelated to these entities. If user intends to modify model entities, capture and return their intent according to provided response schema. If the intent is to unset a field - return default value for this field according to schema."},
        {"role": "system", "content": combined_entity_ctx},
        {"role": "user", "content": input_text},
    ]

    llm_client = client or OpenAI()

    completion = llm_client.chat.completions.parse(
        model="gpt-4o",
        messages=messages,
        response_format=LlmStateDiffs,
        temperature=0.0
    )

    llm_response: LlmStateDiffs = completion.choices[0].message.parsed
    entity_class_map = {ctx.entity_class.__name__: ctx.entity_class for ctx in entity_contexts}

    return [
        StateDiff(
            entity_class=entity_class_map[llm_diff.entity_class_name],
            entity_ref=llm_diff.entity_ref,
            diffs=llm_diff.diffs,
        )
        for llm_diff in llm_response.diffs
        if llm_diff.entity_class_name in entity_class_map
    ]


def register_llm_parser(channel_domain: str | None = None) -> None:
    from agent.parser.parser_registry import register_parser

    register_parser(
        LlmParser(
            channel_domains=[channel_domain] if channel_domain is not None else [None]
        )
    )

