from typing import Annotated
from pydantic import BaseModel

# marker
class ExtractsTo:
    def __init__(self, *entities): self.entities = entities

# generic-like alias: InputField[T, EntA, EntB, ...] -> Annotated[T, ExtractsTo(...)]
class InputField:
    def __class_getitem__(cls, params):
        if not isinstance(params, tuple):
            params = (params,)
        tp, *entities = params
        return Annotated[tp, ExtractsTo(*entities)]

# base model with helper
class BaseInput(BaseModel):
    @classmethod
    def get_extracts_mapping(cls) -> dict[str, list[type[BaseModel]]]:
        mapping: dict[str, list[type[BaseModel]]] = {}
        for name, f in cls.model_fields.items():
            for m in f.metadata:
                if isinstance(m, ExtractsTo):
                    mapping[name] = list(m.entities)
        return mapping

# --- example usage ---
class Ent1(BaseModel): ...
class Ent2(BaseModel): ...
class Ent3(BaseModel): ...
class Ent4(BaseModel): ...
class Ent5(BaseModel): ...
class SlackInteraction(BaseModel): ...

class KbInput(BaseInput):
    call_transcript: InputField[str, Ent1, Ent2]
    slack_interactions: InputField[list[SlackInteraction], Ent3, Ent4, Ent5]

# mapping:
# {'call_transcript': [Ent1, Ent2], 'slack_interactions': [Ent3, Ent4, Ent5]}
