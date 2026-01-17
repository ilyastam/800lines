import shutil
import unittest

from agent.interaction.channel import TerminalChannel
from agent.interaction.output.controller.llm_chat_outputs_controller import LlmChatOutputsController
from agent.interaction.output.llm_output import ChatOutput
from agent.state.entity.actor.base_actor import BaseActor
from agent.state.controller.base_state_controller import BaseStateController
from agent.state.storage.one_entity_per_type_storage import OneEntityPerTypeStorage
from examples.boat_booking.input import BoatBookingInput
from examples.boat_booking.state_entity import BoatSpecEntity, DesiredLocationEntity, DatesAndDurationEntity


class TestBoatBooking(unittest.TestCase):
    def test_clear_model_field(self):
        terminal_width = shutil.get_terminal_size().columns
        wrap_width = int(terminal_width * 0.8)
        message = "I want to book a 40 ft catamaran in Split Croatia for July 10th, 2026"
        terminal_channel = TerminalChannel()
        BoatBookingInput.channel = terminal_channel
        bb_input = BoatBookingInput(input_value=message)

        state_controller = BaseStateController(storage=OneEntityPerTypeStorage(
            entity_classes=[DesiredLocationEntity, BoatSpecEntity, DatesAndDurationEntity]
        ))
        outputs_controller = LlmChatOutputsController(
            state_controller=state_controller,
            output_channel=terminal_channel,
            wrap_width=wrap_width,
        )

        user_actor = BaseActor(id="user")

        outputs_controller.record_output(
            ChatOutput(input_value=message, channel_instance=terminal_channel, actor=user_actor)
        )
        state_controller.record_outputs(
            ChatOutput(input_value=message, channel_instance=terminal_channel, actor=user_actor)
        )
        state_controller.record_input(bb_input)
        changes, tasks = state_controller.update_state([bb_input])

        interactions = outputs_controller.generate_outputs(changes, tasks)
        interaction = interactions[0]
        outputs_controller.record_output(
            ChatOutput(input_value=interaction.input_value, channel_instance=terminal_channel)
        )
        state_controller.record_outputs(
            ChatOutput(input_value=interaction.input_value, channel_instance=terminal_channel)
        )

        unset_field_message = "No actually I changed my mind about 40ft"

        bb_input = BoatBookingInput(input_value=unset_field_message)
        state_controller.record_input(bb_input)

        outputs_controller.record_output(
            ChatOutput(input_value=message, channel_instance=terminal_channel, actor=user_actor)
        )
        state_controller.record_outputs(
            ChatOutput(input_value=message, channel_instance=terminal_channel, actor=user_actor)
        )
        changes, tasks = state_controller.update_state([bb_input])

        pass


if __name__ == '__main__':
    unittest.main()
