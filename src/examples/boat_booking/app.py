import textwrap
import json

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
    message = "I want to book a 40 ft catamaran in Split Croatia for July 10th, 2026"
    bb_input = BoatBookingInput(chat_message=message)

    state_controller = BaseStateController(storage=BBStateStorage())
    interactions_controller = LlmInteractionsController(state_controller=state_controller)

    changes = state_controller.compute_state(bb_input)
    interactions_controller.record_interaction({'role': 'user', 'content': message})
    interactions = interactions_controller.generate_interaction(changes)
    print(interactions)
