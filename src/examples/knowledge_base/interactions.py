from pydantic import BaseModel

# this is an example for now
class SlackInteraction(BaseModel):
    author: str
    text: str