from typing import ClassVar

from agent.inputs import BaseInput, InputField
from agent.interaction.channel import BaseChannel
from examples.knowledge_base.interactions import SlackInteraction
from examples.knowledge_base.state_entities import Task, Decision


class KbInput(BaseInput):
    channel: ClassVar[BaseChannel] = BaseChannel(
        channel_domain="knowledge-base",
        channel_id="kb-default",
        input_context={},
        output_context={},
    )
    call_transcript: InputField[str | None, Task, Decision] = None
    slack_interactions: InputField[list[SlackInteraction] | None, Task, Decision] = None
