from typing import ClassVar

from agent.inputs import BaseInput
from agent.interaction.channel import BaseChannel
from examples.knowledge_base.state_entities import Task, Decision


class KbInput(BaseInput):
    channel: ClassVar[BaseChannel] = BaseChannel(
        channel_domain="knowledge-base",
        channel_id="kb-default",
        input_context=(),
        output_context=(),
    )
    extracts_to: ClassVar[set] = {Task, Decision}
    input_value: str
