from agent.inputs import BaseInput, InputField
from examples.knowledge_base.interactions import SlackInteraction
from examples.knowledge_base.state_entities import Task, Decision


class KbInput(BaseInput):
    call_transcript: InputField[str | None, Task, Decision] = None
    slack_interactions: InputField[list[SlackInteraction] | None, Task, Decision] = None
