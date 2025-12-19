from __future__ import annotations

from typing import Callable

from agent.interaction.channel.base_channel_connector import BaseChannelConnector
from agent.interaction.llm_interaction import ChatInteraction


class BoatBookingTUIConnector(BaseChannelConnector):
    """Send chat interactions into :class:`BoatBookingTUI` instances."""

    def __init__(self, emit_message: Callable[[str, bool], None]):
        """
        Args:
            emit_message: Callable that accepts the message content and a flag
                indicating whether it came from the user. This matches the
                ``add_chat_message`` signature on ``BoatBookingTUI`` and can be
                wrapped with ``call_from_thread`` when threading.
        """

        super().__init__({ChatInteraction})
        self.emit_message = emit_message

    def emit(self, interaction: ChatInteraction):
        is_user = getattr(interaction, "role", "") == "user"
        self.emit_message(str(interaction.content), is_user)
