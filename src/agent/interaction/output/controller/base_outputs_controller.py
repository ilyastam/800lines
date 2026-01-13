from abc import ABC, abstractmethod
from agent.interaction.output.base_output import BaseOutput
from agent.interaction.channel.channel import BaseChannel
from agent.state.entity.state_entity import BaseStateEntity
from agent.parser.state_diff import StateDiff


class BaseOutputsController(ABC):

    def __init__(self, output_channel: BaseChannel):
        self.output_channel = output_channel

    @abstractmethod
    def get_state_controller(self):
        pass

    @abstractmethod
    def generate_outputs(self, state_diffs: list[StateDiff], max_outputs: int | None = None) -> list[BaseOutput]:
        pass

    @abstractmethod
    def generate_output(self, entity: BaseStateEntity, state_diff: StateDiff | None) -> BaseOutput:
        pass

    def is_applicable_(self, output_channel: BaseChannel | None) -> bool:
        """Return True when this controller can handle the given channel."""

        return output_channel is not None and output_channel == self.output_channel

    def emit_relevant_outputs(self, outputs: list[BaseOutput]) -> list[BaseOutput]:
        emitted_outputs: list[BaseOutput] = []
        for output in outputs:
            output_channel = output.get_channel()
            if not self.is_applicable_(output_channel):
                continue

            emitted_output: BaseOutput | None = self.emit_output(output)
            if emitted_output:
                emitted_outputs.append(emitted_output)
        return emitted_outputs

    @abstractmethod
    def emit_output(self, output: BaseOutput) -> BaseOutput | None:
        pass
