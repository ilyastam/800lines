

from agent.inputs import BaseInput
from agent.interaction.base_interaction import BaseInteraction
from agent.interaction.channel.dispatcher import ChannelDispatcher
from agent.interaction.controller.base_interactions_controller import BaseInteractionsController
from agent.state.controller.base_state_controller import BaseStateController
from agent.state.entity.types import MutationIntent


class BaseAgent:

    def __init__(self,
                 state_controller: BaseStateController,
                 interactions_controller: BaseInteractionsController,
                 channel_dispatcher: ChannelDispatcher | None = None):
        self.state_controller = state_controller
        self.interactions_controller = interactions_controller
        self.channel_dispatcher = channel_dispatcher

    def consume_inputs(self, inputs: list[BaseInput]) -> list[BaseInteraction]: # tuple[ObjectiveStatus, list[Interaction]]:
        changes: list[MutationIntent] = self.state_controller.update_state(inputs)
        interactions = self.interactions_controller.generate_interactions(changes)
        return interactions

    def emit_interactions(self, interactions: list[BaseInteraction]) -> None:
        if not self.channel_dispatcher:
            return

        self.channel_dispatcher.dispatch(interactions)

    def run_cycle(self, inputs: list[BaseInput]):
        interactions: list[BaseInteraction] = self.consume_inputs(inputs)
        self.emit_interactions(interactions)
        return self.state_controller.is_state_completed()

    def is_done(self) -> bool:
        return self.state_controller.is_state_completed()


