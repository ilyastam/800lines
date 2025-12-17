from agent.state.controller.base_state_controller import BaseStateController
from examples.knowledge_base.input import KbInput


if __name__ == '__main__':
    kb_input = KbInput(
        call_transcript="We decided to use mysql, Jack will handle the install. We also agreed to have pizza for lunch."
    )

    bsc = BaseStateController()

    print(kb_input.get_extracts_mapping())
    bsc.compute_state(kb_input)

    #Next: parse state entities from input