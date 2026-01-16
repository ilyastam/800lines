from datetime import datetime
from typing import Literal
from agent.state.entity.state_entity import BaseStateEntity
from pydantic import Field


class DesiredLocationEntity(BaseStateEntity):
    country: str | None = Field(default=None, description="Country where user intends to charter a boat")
    region: str | None = Field(default=None, description="Region where user intends to charter a boat - this is like state in the US")
    city: str | None = Field(default=None, description="City where user intends to charter a boat")


class BoatSpecEntity(BaseStateEntity):
    boat_type: Literal['monohull', 'catamaran', 'unknown'] = Field(default='unknown', description="Boat type requested by the user")
    boat_length_ft: int | None = Field(default=None, description="Boat length requested by the user")
    number_of_cabins: int | None = Field(default=None, description="Number of cabins requested by the user")

    def is_completed(self) -> bool:
        return self.boat_type != 'unknown' and self.boat_length_ft is not None and self.number_of_cabins is not None


class DatesAndDurationEntity(BaseStateEntity):
    trip_start_date: datetime | None = Field(default=None, description="Start date of the trip requested by the user")
    trip_end_date: datetime | None = Field(default=None, description="End date of the trip requested by the user")
    number_of_days: int | None = Field(default=None, description="Trip duration in days requested by the user")
