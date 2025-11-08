from agent.inputs import BaseInput
from agent.llp_parser import parse_state_models_with_llm
from agent.state_entity import BaseStateEntity, LlmParsedStateEntity


class BaseStateController:
    def compute_state(self, input: BaseInput):
        input_fields_to_state_models: dict[str, list[type[BaseStateEntity]]] = input.get_extracts_mapping()
        for input_field_name, state_model_classes in input_fields_to_state_models.items():
            input_field_value = getattr(input, input_field_name)

            if not input_field_value:
                continue

            llp_parseable_models: list[type[LlmParsedStateEntity]] = list(filter(
                lambda model_class: issubclass(model_class, LlmParsedStateEntity),
                state_model_classes
            ))

            parsed_models = parse_state_models_with_llm(input_field_value, llp_parseable_models)
            pass


    def udpate_state(self, state_models: list[BaseStateEntity]):
        pass