from datetime import datetime

from pydantic import BaseModel, Field


class _CalendarEventBase(BaseModel):
    summary: str | None = Field(None, description="Event title")
    start_time: datetime | None = Field(
        None, description="Start datetime for timed events"
    )
    end_time: datetime | None = Field(None, description="End datetime for timed events")
    description: str | None = Field(None, description="Event description")
    location: str | None = Field(None, description="Event location")


class CalendarEvent(_CalendarEventBase):
    id: str | None = Field(None, description="Google Calendar event ID")
    summary: str = Field(..., description="Event title")
    is_all_day: bool = Field(False, description="Whether it's an all-day event")


class CalendarEventList(BaseModel):
    events: list[CalendarEvent] = Field(..., description="List of calendar events")
    count: int = Field(..., description="Number of events")


class EventsRangeRequest(BaseModel):
    start: datetime = Field(..., description="Start datetime (ISO 8601)")
    end: datetime = Field(..., description="End datetime (ISO 8601)")


class CalendarEventCreate(_CalendarEventBase):
    """Schema for creating a new calendar event."""

    summary: str = Field(..., description="Event title")
    is_all_day: bool = Field(False, description="Whether it's an all-day event")


class CalendarEventUpdate(_CalendarEventBase):
    """Schema for updating an existing calendar event (all fields optional)."""

    pass


class CalendarEventResponse(CalendarEvent):
    """Schema for calendar event creation response.

    Extends CalendarEvent with the html_link field for the Google Calendar URL.
    """

    html_link: str = Field(..., description="Link to the event in Google Calendar")
