from datetime import datetime
from typing import Literal
from agent.state_entity import LlmParsedStateEntity
from pydantic import BaseModel, Field


class DesiredLocation(BaseModel):
    country: str
    region: str
    city: str


class BoatSpec(BaseModel):
    boat_type: Literal['monohull', 'catamaran', 'unknown'] = Field(default='unknown', description="Boat type requested by the user")
    boat_length_ft: int | None = Field(default=None, description="Boat length requested by the user")
    number_of_cabins: int | None = Field(default=None, description="Number of cabins requested by the user")


class DatesAndDuration(BaseModel):
    trip_start_date: datetime | None = Field(default=None, description="Start date of the trip requested by the user")
    trip_end_date: datetime | None = Field(default=None, description="End date of the trip requested by the user")
    number_of_days: int | None = Field(default=None, description="Trip duration in days requested by the user")


class DesiredLocationEntity(LlmParsedStateEntity[DesiredLocation]):
    pass


class BoatSpecEntity(LlmParsedStateEntity(BaseModel)):
    pass


class DatesAndDurationEntity(LlmParsedStateEntity(DatesAndDuration)):
    pass
