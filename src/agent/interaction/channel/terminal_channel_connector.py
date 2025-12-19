from __future__ import annotations

import shutil
import textwrap

from agent.interaction.channel.base_channel_connector import BaseChannelConnector
from agent.interaction.llm_interaction import ChatInteraction


class TerminalChannelConnector(BaseChannelConnector):
    """Simple connector that writes interactions to the terminal."""

    def __init__(self, wrap_width: int | None = None):
        super().__init__({ChatInteraction})
        self.wrap_width = wrap_width

    def emit(self, interaction: ChatInteraction):
        width = self.wrap_width or max(int(shutil.get_terminal_size().columns * 0.8), 20)
        role = getattr(interaction, "role", "")
        role_prefix = f"{role.title()}: " if role else ""
        message = f"{role_prefix}{interaction.content}"
        print(textwrap.fill(message, width=width))
