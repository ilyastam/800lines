from typing import ClassVar

from pydantic import Field
from agent.state_entity import DefaultStateEntityContext, LlmParsedStateEntity


class Task(LlmParsedStateEntity[str, DefaultStateEntityContext]):
    definition: ClassVar[str] = """
        Describes an action that needs to be executed in the future based on the context.
        Examples: 
        "Migrate database from crdb to postgres"
        "Draft a doc for vendor user training"
        "Send a release email"

        Task can be assigned to zero or more people. 
    """

    assignees: list[str] = Field(default_factory=list)


class Decision(LlmParsedStateEntity[str, DefaultStateEntityContext]): 
    definition: ClassVar[str] = """
        Describes a decision that participants of the conversation reached.

        Examples:
        "Let's punt work on API migration to the next quarter"
        "Billing API will always run fraud detection model on every payment"
    """
