from typing import Any

from agent.interaction.channel.channel import BaseChannel
from agent.interaction.interaction import Interaction


class BaseOutput(Interaction):
    input_value: Any
    channel_instance: BaseChannel | None = None

    def get_channel(self) -> BaseChannel | None:
        return self.channel_instance or super().get_channel()
