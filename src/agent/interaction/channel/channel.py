from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from agent.state.entity.actor.base_actor import BaseActor


class BaseChannel(BaseModel):
    """Represents a source and destination for outputs and inputs."""

    model_config = ConfigDict(frozen=True)

    channel_domain: str
    channel_id: str
    input_context: tuple[tuple[str, str], ...] = Field(default_factory=tuple)
    output_context: tuple[tuple[str, str], ...] = Field(default_factory=tuple)
    description: str | None = None

    def create_output(self, content: str, actor: BaseActor | None = None) -> "BaseOutput":
        """Create a channel-bound output instance."""

        raise NotImplementedError("BaseChannel must define create_output")


class TerminalChannel(BaseChannel):
    """Default channel for single-session terminal outputs."""

    def __init__(self, channel_id: str | None = None):
        super().__init__(
            channel_domain="terminal",
            channel_id=channel_id or "terminal",
            input_context=(),
            output_context=(),
            description="Local terminal session",
        )

    def create_output(self, content: str, actor: "BaseActor | None" = None) -> "BaseOutput":
        from agent.interaction.output.llm_output import ChatOutput

        if actor is None:
            return ChatOutput(input_value=content, channel_instance=self)
        return ChatOutput(input_value=content, channel_instance=self, actor=actor)
