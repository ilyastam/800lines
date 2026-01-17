from typing import Any, ClassVar

from agent.interaction.interaction import Interaction
from agent.state.entity.state_entity import BaseStateEntity


class BaseInput(Interaction):
    extracts_to: ClassVar[set[type[BaseStateEntity]]]
    input_value: Any

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if "extracts_to" not in cls.__dict__:
            raise TypeError(f"{cls.__name__} must define a class-level 'extracts_to'")

        extracts_to_value = cls.__dict__["extracts_to"]
        if not isinstance(extracts_to_value, set):
            raise TypeError(
                f"{cls.__name__}.extracts_to must be a set of BaseStateEntity subclasses (can be empty for task-only inputs)"
            )
