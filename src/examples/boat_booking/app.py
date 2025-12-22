import json
import shutil

from pydantic import BaseModel

from agent.base_agent import BaseAgent
from agent.interaction.channel import ChannelDispatcher, TerminalChannel, TerminalChannelConnector
from agent.interaction.controller.llm_chat_interactions_controller import LlmChatInteractionsController
from agent.state.controller.base_state_controller import BaseStateController
from agent.state.storage.one_entity_per_type_storage import OneEntityPerTypeStorage
from examples.boat_booking.actor import CustomerActor
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

    terminal_channel = BoatBookingInput.channel
    customer = CustomerActor(id='customer-001', name='John Doe', email='john@example.com')
    message = "I want to book a 40 ft catamaran in Split Croatia for July 10th, 2026"
    bb_input = BoatBookingInput(input_value=message, actor=customer)

    state_controller = BaseStateController(storage=OneEntityPerTypeStorage(
        entity_classes=[DesiredLocationEntity, BoatSpecEntity, DatesAndDurationEntity]
    ))
    interactions_controller = LlmChatInteractionsController(
        state_controller=state_controller,
        input_channels={terminal_channel},
        output_channel=terminal_channel,
    )
    channel_dispatcher = ChannelDispatcher([
        TerminalChannelConnector(wrap_width=wrap_width, channel=terminal_channel)
    ])

    agent = BaseAgent(
        state_controller=state_controller,
        interactions_controller=interactions_controller,
        channel_dispatcher=channel_dispatcher
    )

    while not agent.is_done():
        changes = state_controller.update_state([bb_input])
        interactions_controller.record_input(bb_input)
        if state_controller.is_state_completed():
            print("We are done here")
            break
        interactions = interactions_controller.generate_interactions(changes)
        interaction = interactions[0]
        interactions_controller.record_interaction(interaction)
        channel_dispatcher.dispatch([interaction])
        message = input(">")
        bb_input = BoatBookingInput(input_value=message, context=[interaction], actor=customer)

    for entity in state_controller.storage.get_all():
        print(f"{type(entity).__name__}: {entity.content.model_dump()}")
        print(f"  Actors: {[actor.model_dump() for actor in entity.actors]}")


# TODO: do I need an agent class to tie together state controller and interactions controller ? - yes
# think about how to implement channel dispatchers, and how to connect emit to terminal in basic and fancy scenario
# test input contexts
