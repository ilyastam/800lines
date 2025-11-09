from agent.inputs import BaseInput, InputField
from examples.boat_booking.state_entity import DesiredLocationEntity, BoatSpecEntity, DatesAndDurationEntity


class BoatBookingInput(BaseInput):
    chat_message: InputField[str | None, DesiredLocationEntity, BoatSpecEntity, DatesAndDurationEntity] = None