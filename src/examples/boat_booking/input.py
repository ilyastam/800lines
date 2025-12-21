from typing import ClassVar

from agent.inputs import BaseInput
from agent.interaction.channel import TerminalChannel
from agent.interaction.llm_interaction import ChatInteraction
from examples.boat_booking.state_entity import DesiredLocationEntity, BoatSpecEntity, DatesAndDurationEntity
from pydantic import Field


class BoatBookingInput(BaseInput):
    channel: ClassVar[TerminalChannel] = TerminalChannel()
    extracts_to: ClassVar[set] = {DesiredLocationEntity, BoatSpecEntity, DatesAndDurationEntity}
    input_value: str
    context: list[ChatInteraction] = Field(default_factory=list)
