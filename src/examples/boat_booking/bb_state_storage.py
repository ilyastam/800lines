from datetime import datetime

from agent.state_entity import BaseStateEntity
from agent.state_storage import StateStorage, EmbeddingService
from agent.state_storage.state_change import StateChange, compare_entities
from examples.boat_booking.state_entity import BoatSpecEntity, DesiredLocationEntity, DatesAndDurationEntity


class BBStateStorage(StateStorage):

    def __init__(self):
        self.boat_spec: BoatSpecEntity | None = None
        self.location: DesiredLocationEntity | None = None
        self.dates_and_duration: DatesAndDurationEntity | None = None

    def add_entities(self, entities: list[BaseStateEntity]) -> list[StateChange]:
        state_changes: list[StateChange] = []

        for entity in entities:
            state_change: StateChange | None = None

            match entity:
                case BoatSpecEntity():
                    state_change = self.boat_spec.merge(entity)
                case DesiredLocationEntity():
                    state_change = self.location.merge(entity)
                case DatesAndDurationEntity():
                    state_change = self.dates_and_duration.merge(entity)

            if state_change:
                state_changes.append(state_change)

        return state_changes

    def get_current_version(self) -> int:
        pass

    def increment_version(self) -> int:
        pass

    def get_version_timestamp(self, version: int) -> datetime | None:
        pass

    def get_entity_version(self, entity_id: str) -> int | None:
        pass

    def get_similar(self, entity: BaseStateEntity, threshold: float = 0.8, limit: int = 10,
                    order_by: str = "similarity") -> list[tuple[BaseStateEntity, float]]:
        pass

    def get_by_id(self, entity_id: str) -> BaseStateEntity | None:
        pass

    def get_all(self, chronological: bool = True) -> list[BaseStateEntity]:
        return [self.boat_spec, self.location, self.dates_and_duration]

    def get_chronological_range(self, start_index: int = 0, limit: int | None = None) -> list[BaseStateEntity]:
        pass

    def to_json(self) -> dict:
        pass

    @classmethod
    def from_json(cls, data: dict, embedding_service: EmbeddingService) -> 'StateStorage':
        pass
