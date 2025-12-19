from typing import Any

from pydantic import BaseModel


class BaseInteraction(BaseModel):
    content: Any


