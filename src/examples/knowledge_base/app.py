from examples.knowledge_base.input import KbInput


if __name__ == '__main__':
    kb_input = KbInput(
        call_transcript = "We decided to use mysql"
    )

    print(kb_input.get_extracts_mapping())
    

    #Next: parse state antities from input