import shutil
import textwrap
import unittest

from agent.interaction_controller import LlmInteractionsController
from agent.state_controller import BaseStateController
from examples.boat_booking.bb_state_storage import BBStateStorage
from examples.boat_booking.input import BoatBookingInput


class TestBoatBooking(unittest.TestCase):
    def test_clear_model_field(self):
        terminal_width = shutil.get_terminal_size().columns
        wrap_width = int(terminal_width * 0.8)
        message = "I want to book a 40 ft catamaran in Split Croatia for July 10th, 2026"
        bb_input = BoatBookingInput(chat_message=message)

        state_controller = BaseStateController(storage=BBStateStorage())
        interactions_controller = LlmInteractionsController(state_controller=state_controller)

        interactions_controller.record_interaction({'role': 'user', 'content': message})
        changes = state_controller.compute_state(bb_input)

        interactions = interactions_controller.generate_interactions(changes)
        interaction = interactions[0]
        interactions_controller.record_interaction({'role': 'assistant', 'content': interaction})

        unset_field_message = "No actually I changed my mind about 40ft"

        bb_input = BoatBookingInput(chat_message=unset_field_message, context=[
            {"role": "assistant", "content": str(interaction)},
        ])

        interactions_controller.record_interaction({'role': 'user', 'content': message})
        changes = state_controller.compute_state(bb_input)

        pass


if __name__ == '__main__':
    unittest.main()
