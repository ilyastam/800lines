from agent.inputs import BaseInput, InputField
from agent.interaction.llm_interaction import ChatInteraction
from examples.boat_booking.state_entity import DesiredLocationEntity, BoatSpecEntity, DatesAndDurationEntity
from pydantic import Field


class BoatBookingInput(BaseInput):
    chat_message: InputField[str | None, DesiredLocationEntity, BoatSpecEntity, DatesAndDurationEntity] = None
    context: list[ChatInteraction] = Field(default_factory=list)
