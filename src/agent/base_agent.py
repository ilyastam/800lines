from agent.interaction.base_input import BaseInput
from agent.interaction.base_output import BaseOutput
from agent.interaction.channel.channel import BaseChannel
from agent.interaction.controller.base_outputs_controller import BaseOutputsController
from agent.state.controller.base_state_controller import BaseStateController
from agent.state.entity.types import MutationIntent


class BaseAgent:

    def __init__(self,
                 state_controller: BaseStateController,
                 output_controllers: list[BaseOutputsController] | tuple[BaseOutputsController, ...]):
        self.state_controller = state_controller
        self.output_controllers = list(output_controllers)

    def consume_inputs(self, inputs: list[BaseInput]) -> list[BaseOutput]:
        filtered_inputs: list[BaseInput] = []
        for input_obj in inputs:
            self.state_controller.record_input(input_obj)
            filtered_inputs.append(input_obj)

        changes: list[MutationIntent] = self.state_controller.update_state(filtered_inputs)

        outputs: list[BaseOutput] = []
        for controller in self.output_controllers:
            outputs.extend(controller.generate_outputs(changes))

        for output in outputs:
            self.state_controller.record_output(output)
        return outputs

    def emit_outputs(self, outputs: list[BaseOutput]) -> None:
        self.dispatch_outputs(outputs)

    def dispatch_outputs(self, outputs: list[BaseOutput]) -> None:
        channel_to_outputs: dict[BaseChannel, list[BaseOutput]] = {}

        for output in outputs:
            output_channel = output.get_channel()
            if output_channel is None:
                continue

            channel_to_outputs.setdefault(output_channel, []).append(output)

        for controller in self.output_controllers:
            for channel, channel_outputs in channel_to_outputs.items():
                if controller.is_applicable_(channel):
                    controller.emit_relevant_outputs(channel_outputs)

    def run_cycle(self, inputs: list[BaseInput]):
        outputs: list[BaseOutput] = self.consume_inputs(inputs)
        self.dispatch_outputs(outputs)
        return self.state_controller.is_state_completed()

    def is_done(self) -> bool:
        return self.state_controller.is_state_completed()
