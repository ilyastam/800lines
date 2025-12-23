from __future__ import annotations

from typing import Iterable

from agent.interaction.base_output import BaseOutput
from agent.interaction.controller.base_outputs_controller import BaseOutputsController


class ChannelDispatcher:
    """Dispatch outputs to the registered controllers."""

    def __init__(self, controllers: Iterable[BaseOutputsController] | None = None):
        self.controllers: list[BaseOutputsController] = list(controllers or [])

    def register(self, controller: BaseOutputsController) -> None:
        """Register an additional controller."""

        self.controllers.append(controller)

    def dispatch(self, outputs: list[BaseOutput]) -> None:
        """Send outputs to every controller that can handle them."""

        for controller in self.controllers:
            controller.emit_relevant_outputs(outputs)
