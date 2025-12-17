from typing import Any

from pydantic import BaseModel, Field

class BaseInteraction(BaseModel):
    channel: str
    target: str | None
    

