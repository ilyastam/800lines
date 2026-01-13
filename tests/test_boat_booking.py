import shutil
import unittest

from agent.interaction.channel import TerminalChannel
from agent.interaction.output.controller.llm_chat_outputs_controller import LlmChatOutputsController
from agent.interaction.output.llm_output import ChatOutput
from agent.parser.llm_parser import parse_state_diff_with_llm
from agent.parser.entity_context import EntityContext
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
        changes = state_controller.update_state([bb_input])

        interactions = outputs_controller.generate_outputs(changes)
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
        changes = state_controller.update_state([bb_input])

        pass

    def test_state_diffs_set_fields(self):
        message = "I want to book a 40ft catamaran"

        model_ctx = EntityContext(
            entity_class=BoatSpecEntity,
            entity_schema=BoatSpecEntity.model_json_schema(),
        )
        state_diffs = parse_state_diff_with_llm(
            input_text=message,
            entity_contexts=[model_ctx],
        )

        all_diffs = [d for state_diff in state_diffs for d in state_diff.diffs]
        diffs_by_field = {d.field_name: d.new_value for d in all_diffs}
        self.assertEqual(diffs_by_field.get('boat_length_ft'), 40)
        self.assertEqual(diffs_by_field.get('boat_type'), 'catamaran')

    def test_state_diffs_unset_fields(self):
        message = "Actually no, I've changed my mind about 40ft"

        model_ctx = EntityContext(
            entity_class=BoatSpecEntity,
            entity_schema=BoatSpecEntity.model_json_schema(),
        )
        state_diffs = parse_state_diff_with_llm(
            input_text=message,
            entity_contexts=[model_ctx],
            context=[{'role': 'user', 'content': 'I want to book a 40ft catamaran'}]
        )

        all_diffs = [d for state_diff in state_diffs for d in state_diff.diffs]
        diffs_by_field = {d.field_name: d.new_value for d in all_diffs}
        self.assertIsNone(diffs_by_field.get('boat_length_ft'))


if __name__ == '__main__':
    unittest.main()
