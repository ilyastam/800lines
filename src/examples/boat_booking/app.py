import textwrap
import json
import shutil

from pydantic import BaseModel

from agent.interaction_controller import LlmInteractionsController
from agent.state_controller import BaseStateController
from examples.boat_booking.bb_state_storage import BBStateStorage
from examples.boat_booking.input import BoatBookingInput


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

    state_controller = BaseStateController(storage=BBStateStorage())
    interactions_controller = LlmInteractionsController(state_controller=state_controller)

    while True:
        interactions_controller.record_interaction({'role': 'user', 'content': message})
        changes = state_controller.compute_state(bb_input)
        if state_controller.is_state_completed():
            print("We are done here")
            break
        interaction = interactions_controller.generate_interactions(changes)[0]
        wrapped_text = textwrap.fill(str(interaction), width=wrap_width)
        print(wrapped_text)
        message = input(">")
        bb_input = BoatBookingInput(chat_message=message, context=[
            {"role": "assistant", "content": str(interaction)},
        ])

    for model in state_controller.storage.get_all():
        print(model.model_dump())


# TODO: add last assistant message to the entities llm parser input.