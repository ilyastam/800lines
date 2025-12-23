from __future__ import annotations

import shutil
import textwrap

from agent.interaction.channel.base_channel_connector import BaseChannelConnector
from agent.interaction.channel.channel import TerminalChannel
from agent.interaction.llm_output import ChatOutput


class TerminalChannelConnector(BaseChannelConnector):
    """Simple connector that writes outputs to the terminal."""

    def __init__(self, wrap_width: int | None = None, channel: TerminalChannel | None = None):
        channel = channel or TerminalChannel()
        super().__init__({ChatOutput}, channel)
        self.wrap_width = wrap_width

    def emit(self, output: ChatOutput):
        width = self.wrap_width or max(int(shutil.get_terminal_size().columns * 0.8), 20)
        role = output.get_role()
        role_prefix = f"{role.title()}: " if role else ""
        message = f"{role_prefix}{output.input_value}"
        print(textwrap.fill(message, width=width))
