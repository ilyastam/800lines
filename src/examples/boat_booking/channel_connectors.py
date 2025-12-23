from __future__ import annotations

from typing import Callable

from agent.interaction.channel import TerminalChannel
from agent.interaction.channel.base_channel_connector import BaseChannelConnector
from agent.interaction.llm_output import ChatOutput


class BoatBookingTUIConnector(BaseChannelConnector):
    """Send chat outputs into :class:`BoatBookingTUI` instances."""

    def __init__(self, emit_message: Callable[[str, bool], None], channel: TerminalChannel | None = None):
        """
        Args:
            emit_message: Callable that accepts the message content and a flag
                indicating whether it came from the user. This matches the
                ``add_chat_message`` signature on ``BoatBookingTUI`` and can be
                wrapped with ``call_from_thread`` when threading.
        """

        channel = channel or TerminalChannel()
        super().__init__({ChatOutput}, channel)
        self.emit_message = emit_message

    def emit(self, interaction: ChatOutput):
        is_user = interaction.get_role() == "user"
        self.emit_message(str(interaction.input_value), is_user)
