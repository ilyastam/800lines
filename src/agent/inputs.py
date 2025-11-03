from typing import Annotated
from pydantic import BaseModel

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

    # returns state entities this input model can extract to. 
    @classmethod
    def get_extracts_mapping(cls) -> dict[str, list[type[BaseModel]]]:
        mapping: dict[str, list[type[BaseModel]]] = {}
        for name, f in cls.model_fields.items():
            for m in f.metadata:
                if isinstance(m, ExtractsTo):
                    mapping[name] = list(m.entities)
        return mapping

