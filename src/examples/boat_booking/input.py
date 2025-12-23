from typing import ClassVar

from agent.interaction.input.base_input import BaseInput
from agent.interaction.channel import TerminalChannel
from examples.boat_booking.state_entity import DesiredLocationEntity, BoatSpecEntity, DatesAndDurationEntity


class BoatBookingInput(BaseInput):
    channel: ClassVar[TerminalChannel] = TerminalChannel()
    extracts_to: ClassVar[set] = {DesiredLocationEntity, BoatSpecEntity, DatesAndDurationEntity}
    input_value: str
