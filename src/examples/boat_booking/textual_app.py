from __future__ import annotations
import io
from contextlib import redirect_stdout

from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.binding import Binding
from textual import work

from agent.interaction.controller.llm_chat_interactions_controller import LlmChatInteractionsController
from agent.state.controller.base_state_controller import BaseStateController
from agent.state.entity.types import MutationIntent
from examples.boat_booking.bb_state_storage import BBStateStorage
from examples.boat_booking.input import BoatBookingInput


class BoatBookingTUI(App):
    """Textual TUI for the boat booking assistant."""

    TITLE = "Boat Booking Assistant"

    CSS = """
    #main-container {
        height: 1fr;
    }

    #chat-pane {
        width: 60%;
        border: solid green;
        padding: 1;
    }

    #logs-pane {
        width: 40%;
        border: solid blue;
        padding: 1;
    }

    #user-input {
        dock: bottom;
        margin: 1;
    }

    .user-message {
        background: $primary-darken-2;
        margin: 1 0;
        padding: 1;
    }

    .assistant-message {
        background: $secondary-darken-2;
        margin: 1 0;
        padding: 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear_logs", "Clear Logs"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.state_controller = BaseStateController(storage=BBStateStorage())
        self.interactions_controller = LlmChatInteractionsController(
            state_controller=self.state_controller
        )

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main-container"):
            with VerticalScroll(id="chat-pane"):
                yield Static(
                    "Welcome! I'll help you book a boat. What are you looking for?",
                    classes="assistant-message",
                )
            yield RichLog(id="logs-pane", highlight=True, markup=True)
        yield Input(placeholder="Type your message...", id="user-input")
        yield Footer()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        message = event.value
        if not message.strip():
            return

        input_widget = self.query_one("#user-input", Input)
        input_widget.value = ""

        self.add_chat_message(message, is_user=True)
        self.process_message(message)

    @work(exclusive=True, thread=True)
    def process_message(self, message: str) -> None:
        captured_output = io.StringIO()

        bb_input = self._build_input(message)

        self.interactions_controller.record_interaction({
            "role": "user",
            "content": message,
        })

        with redirect_stdout(captured_output):
            changes = self.state_controller.update_state(bb_input)

        self.call_from_thread(self.log_state_changes, changes)

        if self.state_controller.is_state_completed():
            self.call_from_thread(self.handle_completion)
            return

        with redirect_stdout(captured_output):
            interactions = self.interactions_controller.generate_interactions(changes)

        prompt_output = captured_output.getvalue()
        if prompt_output:
            self.call_from_thread(self.log_llm_prompt, prompt_output)

        if interactions:
            interaction = interactions[0]
            self.interactions_controller.record_interaction({
                "role": "assistant",
                "content": interaction,
            })
            self.call_from_thread(self.add_chat_message, str(interaction), False)

    def add_chat_message(self, content: str, is_user: bool) -> None:
        chat_pane = self.query_one("#chat-pane", VerticalScroll)

        prefix = "You: " if is_user else "Assistant: "
        css_class = "user-message" if is_user else "assistant-message"

        message_widget = Static(f"{prefix}{content}", classes=css_class)
        chat_pane.mount(message_widget)
        chat_pane.scroll_end(animate=False)

    def log_state_changes(self, changes: list[MutationIntent]) -> None:
        logs_pane = self.query_one("#logs-pane", RichLog)

        if not changes:
            logs_pane.write("[dim]No state changes[/dim]")
            return

        for intent in changes:
            logs_pane.write(
                f"[bold yellow]State Change: {intent.entity_class_name}[/bold yellow]"
            )
            for diff in intent.diffs:
                logs_pane.write(f"  [green]{diff.field_name}[/green] = {diff.new_value}")
            if intent.validation_errors:
                for err in intent.validation_errors:
                    logs_pane.write(f"  [red]Error: {err}[/red]")

    def log_llm_prompt(self, prompt: str) -> None:
        logs_pane = self.query_one("#logs-pane", RichLog)

        display_prompt = prompt[:500] + "..." if len(prompt) > 500 else prompt
        logs_pane.write("[dim]--- LLM Prompt ---[/dim]")
        logs_pane.write(f"[dim]{display_prompt}[/dim]")

    def handle_completion(self) -> None:
        chat_pane = self.query_one("#chat-pane", VerticalScroll)
        logs_pane = self.query_one("#logs-pane", RichLog)

        completion_msg = Static(
            "Booking complete! All required information collected.",
            classes="assistant-message",
        )
        chat_pane.mount(completion_msg)

        logs_pane.write("[bold green]--- Final State ---[/bold green]")
        for model in self.state_controller.storage.get_all():
            logs_pane.write(str(model.model_dump()))

        input_widget = self.query_one("#user-input", Input)
        input_widget.disabled = True

    def _build_input(self, message: str) -> BoatBookingInput:
        context: list[dict[str, str]] = []
        if self.interactions_controller.interactions:
            last_interactions = self.interactions_controller.interactions[-2:]
            for interaction in last_interactions:
                if interaction.get("role") == "assistant":
                    context.append({
                        "role": "assistant",
                        "content": str(interaction.get("content", "")),
                    })

        return BoatBookingInput(chat_message=message, context=context)

    def action_clear_logs(self) -> None:
        logs_pane = self.query_one("#logs-pane", RichLog)
        logs_pane.clear()


def main() -> None:
    app = BoatBookingTUI()
    app.run()


if __name__ == "__main__":
    main()
