from typing import ClassVar, Literal

from pydantic import Field

from agent.interaction.base_interaction import BaseInteraction
from agent.interaction.channel import TerminalChannel


class ChatInteraction(BaseInteraction):
    channel: ClassVar[TerminalChannel] = TerminalChannel()
    role: Literal['user', 'assistant', 'system'] = Field(default='user')
    content: str

    def to_llm_message(self) -> dict[str, str]:
        return {
            'role': self.role,
            'content': self.content
        }
