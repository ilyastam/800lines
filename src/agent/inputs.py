from typing import Any, ClassVar
from pydantic import BaseModel, Field

from agent.interaction.channel.channel import BaseChannel
from agent.state.entity.actor.base_actor import BaseActor
from agent.state.entity.actor.default_actor import DefaultActor
from agent.state.entity.state_entity import BaseStateEntity


class BaseInput(BaseModel):
    channel: ClassVar[BaseChannel]
    extracts_to: ClassVar[set[type[BaseStateEntity]]]
    input_value: Any
    context: Any | None = None
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

        if "extracts_to" not in cls.__dict__:
            raise TypeError(f"{cls.__name__} must define a class-level 'extracts_to'")

        extracts_to_value = cls.__dict__["extracts_to"]
        if not isinstance(extracts_to_value, set) or not extracts_to_value:
            raise TypeError(
                f"{cls.__name__}.extracts_to must be a non-empty set of BaseStateEntity subclasses"
            )
