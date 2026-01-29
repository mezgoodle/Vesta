from datetime import datetime

from pydantic import BaseModel, Field


class CalendarEvent(BaseModel):
    summary: str = Field(..., description="Event title")
    start_time: datetime | None = Field(
        None, description="Start datetime for timed events"
    )
    end_time: datetime | None = Field(None, description="End datetime for timed events")
    is_all_day: bool = Field(False, description="Whether it's an all-day event")
    description: str | None = Field(None, description="Event description")
    location: str | None = Field(None, description="Event location")


class CalendarEventList(BaseModel):
    events: list[CalendarEvent] = Field(..., description="List of calendar events")
    count: int = Field(..., description="Number of events")


class EventsRangeRequest(BaseModel):
    start: datetime = Field(..., description="Start datetime (ISO 8601)")
    end: datetime = Field(..., description="End datetime (ISO 8601)")
