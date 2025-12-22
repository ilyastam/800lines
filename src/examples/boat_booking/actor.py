from agent.state.entity.actor.base_actor import BaseActor


class CustomerActor(BaseActor):
    id: str
    name: str | None = None
    email: str | None = None
