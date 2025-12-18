from typing import Annotated, get_origin, get_args, Any
from pydantic import BaseModel

from agent.state.entity.state_entity import BaseStateEntity


# marker
class ExtractsTo:
    def __init__(self, *entities): 
        self.entities = entities


# generic-like alias: InputField[T, EntA, EntB, ...] -> Annotated[T, ExtractsTo(...)]
class InputField:
    def __class_getitem__(cls, params):
        if not isinstance(params, tuple):
            params = (params,)
        tp, *entities = params
        return Annotated[tp, ExtractsTo(*entities)]


# base model with helper
class BaseInput(BaseModel):
    context: Any | None = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        has_input_field = False
        for ann in cls.__annotations__.values():
            if get_origin(ann) is Annotated:
                args = get_args(ann)
                if any(isinstance(arg, ExtractsTo) for arg in args):
                    has_input_field = True
                    break
        if not has_input_field:
            raise TypeError(f"{cls.__name__} must have at least one InputField")

    @classmethod
    def get_extracts_mapping(cls) -> dict[str, list[type[BaseStateEntity]]]:
        mapping: dict[str, list[type[BaseStateEntity]]] = {}
        for name, f in cls.model_fields.items():
            for m in f.metadata:
                if isinstance(m, ExtractsTo):
                    mapping[name] = list(m.entities)
        return mapping

