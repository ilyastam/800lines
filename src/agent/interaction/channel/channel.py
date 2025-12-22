from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from agent.interaction.base_interaction import BaseInteraction
    from agent.state.entity.actor.base_actor import BaseActor


class BaseChannel(BaseModel):
    """Represents a source and destination for interactions and inputs."""

    model_config = ConfigDict(frozen=True)

    channel_domain: str
    channel_id: str
    input_context: tuple[tuple[str, str], ...] = Field(default_factory=tuple)
    output_context: tuple[tuple[str, str], ...] = Field(default_factory=tuple)
    description: str | None = None

    def create_interaction(self, role: str, content: str, actor: "BaseActor | None" = None) -> "BaseInteraction":
        """Create a channel-bound interaction instance."""

        raise NotImplementedError("BaseChannel must define create_interaction")


class TerminalChannel(BaseChannel):
    """Default channel for single-session terminal interactions."""

    def __init__(self, channel_id: str | None = None):
        super().__init__(
            channel_domain="terminal",
            channel_id=channel_id or "terminal",
            input_context=(),
            output_context=(),
            description="Local terminal session",
        )

    def create_interaction(self, role: str, content: str, actor: "BaseActor | None" = None) -> "BaseInteraction":
        from agent.interaction.llm_interaction import ChatInteraction

        if actor is None:
            return ChatInteraction(role=role, content=content, channel_instance=self)
        return ChatInteraction(role=role, content=content, channel_instance=self, actor=actor)
