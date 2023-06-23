from datetime import datetime
from pydantic import BaseModel, Field


class EventSchema(BaseModel):
    name: str
    date_event: str
    time_event: str
    place: str
    link: str


class EventInDBSchema(EventSchema):
    id: int = Field(ge=1)
