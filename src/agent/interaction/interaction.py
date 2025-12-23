from typing import ClassVar

from pydantic import BaseModel, Field
from agent.interaction.channel.channel import BaseChannel
from agent.state.entity.actor.base_actor import BaseActor
from agent.state.entity.actor.default_actor import DefaultActor


class Interaction(BaseModel):
    channel: ClassVar[BaseChannel]
    actor: BaseActor = Field(default_factory=DefaultActor)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if "channel" not in cls.__dict__:
            raise TypeError(f"{cls.__name__} must define a class-level 'channel'")

        channel_value = cls.__dict__["channel"]
        if not isinstance(channel_value, BaseChannel):
            raise TypeError(
                f"{cls.__name__}.channel must be set to a BaseChannel instance at class definition time"
            )

    def get_channel(self) -> BaseChannel:
        return self.__class__.channel
