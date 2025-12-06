from datetime import datetime
from typing import Literal
from agent.state_entity import LlmParsedStateEntity, Completable
from pydantic import BaseModel, Field


class DesiredLocation(BaseModel, Completable):
    country: str | None = Field(default=None, description="Country where user intends to charter a boat")
    region: str | None = Field(default=None, description="Region where user intends to charter a boat - this is like state in the US")
    city: str | None = Field(default=None, description="City where user intends to charter a boat")

    def is_completed(self) -> bool:
        return self.country != 'unknown' and self.region and self.city


class BoatSpec(BaseModel, Completable):
    boat_type: Literal['monohull', 'catamaran', 'unknown'] = Field(default='unknown', description="Boat type requested by the user")
    boat_length_ft: int | None = Field(default=None, description="Boat length requested by the user")
    number_of_cabins: int | None = Field(default=None, description="Number of cabins requested by the user")

    def is_completed(self) -> bool:
        return self.boat_type != 'unknown' and self.boat_length_ft and self.number_of_cabins


class DatesAndDuration(BaseModel, Completable):
    trip_start_date: datetime | None = Field(default=None, description="Start date of the trip requested by the user")
    trip_end_date: datetime | None = Field(default=None, description="End date of the trip requested by the user")
    number_of_days: int | None = Field(default=None, description="Trip duration in days requested by the user")

    def is_completed(self) -> bool:
        return self.trip_start_date != 'unknown' and self.trip_end_date and self.number_of_days


class DesiredLocationEntity(LlmParsedStateEntity[DesiredLocation]):
    pass


class BoatSpecEntity(LlmParsedStateEntity[BoatSpec]):
    pass


class DatesAndDurationEntity(LlmParsedStateEntity[DatesAndDuration]):
    pass
