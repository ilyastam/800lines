from __future__ import annotations

from datetime import datetime

from agent.state_entity import BaseStateEntity
from agent.state_storage import StateStorage, EmbeddingService
from agent.types import MutationIntent
from examples.boat_booking.state_entity import BoatSpecEntity, DesiredLocationEntity, DatesAndDurationEntity


class BBStateStorage(StateStorage):

    def __init__(self):
        self.boat_spec: BoatSpecEntity | None = None
        self.location: DesiredLocationEntity | None = None
        self.dates_and_duration: DatesAndDurationEntity | None = None

    def add_intents(self, intents: list[MutationIntent]) -> list[MutationIntent]:
        applied_intents: list[MutationIntent] = []

        for intent in intents:
            applied_intent: MutationIntent | None = None
            match intent.model_class_name:
                case 'BoatSpecEntity':
                    self.boat_spec, applied_intent = BoatSpecEntity.merge(self.boat_spec, intent)
                case 'DesiredLocationEntity':
                    self.location, applied_intent = DesiredLocationEntity.merge(self.location, intent)
                case 'DatesAndDurationEntity':
                    self.dates_and_duration, applied_intent = DatesAndDurationEntity.merge(self.dates_and_duration, intent)

            if applied_intent and applied_intent.diffs:
                applied_intents.append(applied_intent)

        return applied_intents

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
        return [e for e in [self.boat_spec, self.location, self.dates_and_duration] if e is not None]

    def get_chronological_range(self, start_index: int = 0, limit: int | None = None) -> list[BaseStateEntity]:
        pass

    def to_json(self) -> dict:
        pass

    @classmethod
    def from_json(cls, data: dict, embedding_service: EmbeddingService) -> 'StateStorage':
        pass
