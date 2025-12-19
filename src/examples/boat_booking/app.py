import textwrap
import json
import shutil

from pydantic import BaseModel

from agent.interaction.controller.llm_chat_interactions_controller import LlmChatInteractionsController
from agent.interaction.llm_interaction import ChatInteraction
from agent.state.controller.base_state_controller import BaseStateController
from agent.state.storage.one_entity_per_type_storage import OneEntityPerTypeStorage
from examples.boat_booking.input import BoatBookingInput
from examples.boat_booking.state_entity import DesiredLocationEntity, BoatSpecEntity, DatesAndDurationEntity


class PydanticEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        return super().default(obj)

if __name__ == '__main__':

    terminal_width = shutil.get_terminal_size().columns
    wrap_width = int(terminal_width * 0.8)

    message = "I want to book a 40 ft catamaran in Split Croatia for July 10th, 2026"
    bb_input = BoatBookingInput(chat_message=message)

    state_controller = BaseStateController(storage=OneEntityPerTypeStorage(
        entity_classes=[DesiredLocationEntity, BoatSpecEntity, DatesAndDurationEntity]
    ))
    interactions_controller = LlmChatInteractionsController(state_controller=state_controller)

    while True:
        interactions_controller.record_interaction(ChatInteraction(role='user', content=message))
        changes = state_controller.update_state([bb_input])
        if state_controller.is_state_completed():
            print("We are done here")
            break
        interactions = interactions_controller.generate_interactions(changes)
        interaction = interactions[0]
        interactions_controller.record_interaction(interaction)
        wrapped_text = textwrap.fill(str(interaction), width=wrap_width)
        print(wrapped_text)
        message = input(">")
        bb_input = BoatBookingInput(chat_message=message, context=[interaction])

    for model in state_controller.storage.get_all():
        print(model.model_dump())


# TODO: do I need an agent class to tie together state controller and interactions controller ? - yes
# think about how to implement channel dispatchers, and how to connect emit to terminal in basic and fancy scenario
# test input contexts