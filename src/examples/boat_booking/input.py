from typing import ClassVar

from agent.inputs import BaseInput, InputField
from agent.interaction.channel import TerminalChannel
from agent.interaction.llm_interaction import ChatInteraction
from examples.boat_booking.state_entity import DesiredLocationEntity, BoatSpecEntity, DatesAndDurationEntity
from pydantic import Field


class BoatBookingInput(BaseInput):
    channel: ClassVar[TerminalChannel] = TerminalChannel()
    input_value: InputField[str | None, DesiredLocationEntity, BoatSpecEntity, DatesAndDurationEntity] = None
    context: list[ChatInteraction] = Field(default_factory=list)
