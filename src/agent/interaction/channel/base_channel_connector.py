from abc import ABC, abstractmethod

from agent.interaction.base_output import BaseOutput
from agent.interaction.channel.channel import BaseChannel


class BaseChannelConnector(ABC):

    def __init__(self, output_types: set[type[BaseOutput]], channel: BaseChannel):
        self.output_types = output_types
        self.channel = channel

    def emit_relevant(self, outputs: list[BaseOutput]):
        for output in outputs:
            if output.__class__ in self.output_types:
                output_channel = output.get_channel()
                if output_channel is not None and output_channel != self.channel:
                    continue
                self.emit(output)

    @abstractmethod
    def emit(self, output: BaseOutput):
        pass
