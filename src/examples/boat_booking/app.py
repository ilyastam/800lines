import textwrap

from agent.state_controller import BaseStateController
from examples.boat_booking.bb_state_storage import BBStateStorage
from examples.boat_booking.input import BoatBookingInput

if __name__ == '__main__':
    bb_input = BoatBookingInput(
        chat_message=textwrap.dedent("""
        I want to book a 40 ft catamaran in Split Croatia for July 10th, 2026
        """)
    )

    state_controller = BaseStateController(storage=BBStateStorage())
    changes = state_controller.compute_state(bb_input)
    pass