from typing import ClassVar

from agent.interaction.base_output import BaseOutput
from agent.interaction.channel import TerminalChannel


class ChatOutput(BaseOutput):
    channel: ClassVar[TerminalChannel] = TerminalChannel()
    input_value: str
