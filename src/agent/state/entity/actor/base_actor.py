from pydantic import BaseModel


class BaseActor(BaseModel):
    id: str
