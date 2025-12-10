from typing import Any, Union

from openai import OpenAI
from pydantic import create_model
from agent.state_entity import LlmParsedStateEntity

client = OpenAI()


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
