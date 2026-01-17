from agent.interaction.input.base_input import BaseInput
from agent.interaction.output.base_output import BaseOutput
from agent.interaction.channel.channel import BaseChannel
from agent.interaction.output.controller.base_outputs_controller import BaseOutputsController
from agent.state.controller.base_state_controller import BaseStateController
from agent.parser.state_diff import StateDiff
from agent.task.base_task import BaseTask, TaskResult, TaskStatus
from agent.task.task_executor import BaseTaskExecutor


class BaseAgent:

    def __init__(self,
                 state_controller: BaseStateController,
                 output_controllers: list[BaseOutputsController] | tuple[BaseOutputsController, ...],
                 task_executor: BaseTaskExecutor | None = None):
        self.state_controller = state_controller
        self.output_controllers = list(output_controllers)
        self.task_executor = task_executor

    def consume_inputs(self, inputs: list[BaseInput]) -> list[BaseOutput]:
        filtered_inputs: list[BaseInput] = []
        for input_obj in inputs:
            self.state_controller.record_input(input_obj)
            filtered_inputs.append(input_obj)

        parse_result = self.state_controller.parse_inputs(filtered_inputs)

        all_state_diffs = list(parse_result.state_diffs)
        completed_tasks: list[BaseTask] = []

        if self.task_executor and parse_result.tasks:
            task_results: list[TaskResult] = self.task_executor.execute_all(parse_result.tasks)
            for task_result in task_results:
                all_state_diffs.extend(task_result.state_diffs)
                completed_tasks.append(task_result.task)

        applied_diffs = self.state_controller.storage.apply_state_diffs(all_state_diffs)

        tasks_to_store = completed_tasks if completed_tasks else parse_result.tasks
        if tasks_to_store:
            self.state_controller.storage.add_tasks(tasks_to_store)

        outputs: list[BaseOutput] = []
        for output_controller in self.output_controllers:
            outputs.extend(output_controller.generate_outputs(applied_diffs, completed_tasks))

        return outputs

    def dispatch_outputs(self, outputs: list[BaseOutput]) -> None:
        channel_to_outputs: dict[BaseChannel, list[BaseOutput]] = {}

        for output in outputs:
            output_channel = output.get_channel()
            if output_channel is None:
                continue
            channel_to_outputs.setdefault(output_channel, []).append(output)

        for output_controller in self.output_controllers:
            for channel, channel_outputs in channel_to_outputs.items():
                self.state_controller.record_outputs(
                    output_controller.emit_relevant_outputs(channel_outputs)
                )

    def run_cycle(self, inputs: list[BaseInput]) -> bool:
        outputs: list[BaseOutput] = self.consume_inputs(inputs)
        self.dispatch_outputs(outputs)
        return self.state_controller.is_state_completed()

    def is_done(self) -> bool:
        return self.state_controller.is_state_completed()
