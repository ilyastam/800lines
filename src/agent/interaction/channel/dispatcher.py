from __future__ import annotations

from typing import Iterable

from agent.interaction.base_output import BaseOutput
from agent.interaction.channel.base_channel_connector import BaseChannelConnector


class ChannelDispatcher:
    """Dispatch outputs to the registered channel connectors."""

    def __init__(self, connectors: Iterable[BaseChannelConnector] | None = None):
        self.connectors: list[BaseChannelConnector] = list(connectors or [])

    def register(self, connector: BaseChannelConnector) -> None:
        """Register an additional connector."""

        self.connectors.append(connector)

    def dispatch(self, outputs: list[BaseOutput]) -> None:
        """Send outputs to every connector that can handle them."""

        for connector in self.connectors:
            connector.emit_relevant(outputs)
