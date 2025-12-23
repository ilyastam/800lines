from agent.interaction.base_input import BaseInput
from agent.interaction.base_output import BaseOutput
from agent.interaction.channel.dispatcher import ChannelDispatcher
from agent.interaction.controller.base_outputs_controller import BaseOutputsController
from agent.state.controller.base_state_controller import BaseStateController
from agent.state.entity.types import MutationIntent


class BaseAgent:

    def __init__(self,
                 state_controller: BaseStateController,
                 outputs_controller: BaseOutputsController,
                 channel_dispatcher: ChannelDispatcher | None = None):
        self.state_controller = state_controller
        self.outputs_controller = outputs_controller
        self.channel_dispatcher = channel_dispatcher

    def consume_inputs(self, inputs: list[BaseInput]) -> list[BaseOutput]:
        filtered_inputs: list[BaseInput] = []
        for input_obj in inputs:
            if input_obj.channel not in self.outputs_controller.input_channels:
                continue

            self.state_controller.record_input(input_obj)
            filtered_inputs.append(input_obj)

        changes: list[MutationIntent] = self.state_controller.update_state(filtered_inputs)
        outputs = self.outputs_controller.generate_outputs(changes)
        for output in outputs:
            self.state_controller.record_output(output)
        return outputs

    def emit_outputs(self, outputs: list[BaseOutput]) -> None:
        if not self.channel_dispatcher:
            return

        self.channel_dispatcher.dispatch(outputs)

    def run_cycle(self, inputs: list[BaseInput]):
        outputs: list[BaseOutput] = self.consume_inputs(inputs)
        self.emit_outputs(outputs)
        return self.state_controller.is_state_completed()

    def is_done(self) -> bool:
        return self.state_controller.is_state_completed()
