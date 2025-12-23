from typing import ClassVar

from agent.interaction.output.base_output import BaseOutput
from agent.interaction.channel import TerminalChannel
from agent.state.entity.actor.default_actor import DefaultActor


class ChatOutput(BaseOutput):
    channel: ClassVar[TerminalChannel] = TerminalChannel()
    input_value: str

    def get_role(self) -> str:
        return "assistant" if isinstance(self.actor, DefaultActor) else "user"

    def to_llm_message(self) -> dict[str, str]:
        return {
            "role": self.get_role(),
            "content": self.input_value,
        }
