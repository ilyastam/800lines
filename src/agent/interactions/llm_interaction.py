from agent.interactions.base_interaction import BaseInteraction
from typing import Literal
from pydantic import Field


class LlmInteraction(BaseInteraction):
    role: Literal['user', 'assistant', 'system'] = Field(default='user')
    content: str
