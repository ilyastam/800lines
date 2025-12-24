from typing import ClassVar

from pydantic import BaseModel, Field
from agent.interaction.channel.channel import BaseChannel
from agent.state.entity.actor.base_actor import BaseActor
from agent.state.entity.actor.default_actor import DefaultActor


class Interaction(BaseModel):
    channel: ClassVar[BaseChannel]
    actor: BaseActor = Field(default_factory=DefaultActor)

    def get_channel(self) -> BaseChannel:
        return self.__class__.channel
