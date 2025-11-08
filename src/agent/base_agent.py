

from agent.inputs import BaseInput


class BaseAgent():
    
    def gather_input(self) -> BaseInput:
        pass

    def process_input(self, input: BaseInput) -> None: # tuple[ObjectiveStatus, list[Interaction]]:
        input.get_extracts_mapping()
        pass

    def emit_interactions(self, interactions: list[Interaction]) -> None:
        pass


