from typing import Any, ClassVar

from pydantic import BaseModel

from agent.interaction.channel.channel import BaseChannel


class BaseInteraction(BaseModel):
    channel: ClassVar[BaseChannel]

    content: Any
    channel_instance: BaseChannel | None = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if "channel" not in cls.__dict__:
            raise TypeError(f"{cls.__name__} must define a class-level 'channel'")

        channel_value = cls.__dict__["channel"]
        if not isinstance(channel_value, BaseChannel):
            raise TypeError(
                f"{cls.__name__}.channel must be set to a BaseChannel instance at class definition time"
            )

    def get_channel(self) -> BaseChannel | None:
        return self.channel_instance or self.__class__.channel

