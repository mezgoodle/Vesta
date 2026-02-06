import asyncio
from datetime import datetime, time, timedelta
from typing import Any

import pytz
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.crud_user import user as crud_user
from app.schemas.calendar import CalendarEvent, CalendarEventCreate


class GoogleCalendarService:
    """Service for interacting with Google Calendar API."""

    def __init__(self) -> None:
        self.token_uri = "https://oauth2.googleapis.com/token"
        self.timezone = "Europe/Kiev"

    async def _fetch_events_raw(
        self,
        user_id: int,
        time_min: datetime,
        time_max: datetime,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        user = await crud_user.get(db, id=user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        if not user.google_refresh_token:
            raise ValueError(
                f"User {user_id} has not authorized Google Calendar access. "
                "Please complete OAuth flow first."
            )

        service = await self._get_calendar_service(user_id, db)

        try:
            time_min_str = time_min.isoformat() + "Z"
            time_max_str = time_max.isoformat() + "Z"

            events_result = await asyncio.to_thread(
                lambda: (
                    service.events()
                    .list(
                        calendarId="primary",
                        timeMin=time_min_str,
                        timeMax=time_max_str,
                        singleEvents=True,
                        orderBy="startTime",
                    )
                    .execute()
                )
            )

            return events_result.get("items", [])

        except RefreshError as e:
            raise RefreshError(
                f"Failed to refresh access token for user {user_id}. "
                "The refresh token may be expired or revoked. "
                "Please re-authorize the application."
            ) from e
        except HttpError as e:
            raise HttpError(
                resp=e.resp,
                content=e.content,
                uri=e.uri,
            ) from e
        except Exception as e:
            raise Exception(f"Failed to fetch calendar events: {str(e)}") from e

    async def get_today_events(
        self, user_id: int, db: AsyncSession
    ) -> list["CalendarEvent"]:
        now = datetime.utcnow()
        time_min = datetime.combine(now.date(), time.min)
        time_max = datetime.combine(now.date(), time.max)
        events = await self._fetch_events_raw(user_id, time_min, time_max, db)
        return self._format_events(events)

    async def get_upcoming_events(
        self, user_id: int, db: AsyncSession, days: int = 7
    ) -> list["CalendarEvent"]:
        now = datetime.utcnow()
        time_min = now
        time_max = now + timedelta(days=days)
        events = await self._fetch_events_raw(user_id, time_min, time_max, db)
        return self._format_events(events)

    async def get_events_in_range(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        db: AsyncSession,
    ) -> list["CalendarEvent"]:
        if end_date <= start_date:
            raise ValueError("end_date must be after start_date")

        events = await self._fetch_events_raw(user_id, start_date, end_date, db)
        return self._format_events(events)

    async def _get_calendar_service(self, user_id: int, db: AsyncSession):
        user = await crud_user.get(db, id=user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        if not user.google_refresh_token:
            raise ValueError(
                f"User {user_id} has not authorized Google Calendar access. "
                "Please complete OAuth flow first."
            )

        try:
            credentials = Credentials(
                token=None,
                refresh_token=user.google_refresh_token,
                token_uri=self.token_uri,
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET.get_secret_value(),
            )
        except Exception as e:
            raise ValueError(f"Failed to create credentials: {str(e)}") from e

        try:
            return await asyncio.to_thread(
                build, "calendar", "v3", credentials=credentials
            )
        except Exception as e:
            raise ValueError(f"Failed to build calendar service: {str(e)}") from e

    def _format_events(self, events: list[dict[str, Any]]) -> list["CalendarEvent"]:
        formatted_events = []
        for event in events:
            start = event.get("start", {})
            end = event.get("end", {})
            summary = event.get("summary", "No Title")
            description = event.get("description")
            location = event.get("location")

            if "date" in start:
                date_str = start.get("date")
                start_time = None
                end_time = None
                is_all_day = True

                if date_str:
                    try:
                        event_date = datetime.fromisoformat(date_str)
                        start_time = event_date.replace(hour=0, minute=0, second=0)
                    except (ValueError, AttributeError):
                        pass
            else:
                start_time = self._parse_datetime(start.get("dateTime"))
                end_time = self._parse_datetime(end.get("dateTime"))
                is_all_day = False
            calendar_event = CalendarEvent(
                summary=summary,
                start_time=start_time,
                end_time=end_time,
                is_all_day=is_all_day,
                description=description,
                location=location,
            )
            formatted_events.append(calendar_event)

        return formatted_events

    def _parse_datetime(self, dt_string: str | None) -> datetime | None:
        if not dt_string:
            return None

        try:
            if dt_string.endswith("Z"):
                dt_string = dt_string[:-1] + "+00:00"

            return datetime.fromisoformat(dt_string)
        except (ValueError, AttributeError):
            return None

    async def create_event(
        self, user_id: int, event_data: CalendarEventCreate, db: AsyncSession
    ) -> dict[str, Any]:
        """
        Create a new calendar event for the user.

        Args:
            user_id: The ID of the user
            event_data: Event creation data
            db: Database session

        Returns:
            Dictionary containing event details including htmlLink

        Raises:
            ValueError: If user not found or not authenticated
            RefreshError: If token refresh fails
            HttpError: If Google API call fails
        """
        # Get user and validate authentication
        user = await crud_user.get(db, id=user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        if not user.google_refresh_token:
            raise ValueError(
                f"User {user_id} has not authorized Google Calendar access. "
                "Please complete OAuth flow first."
            )

        service = await self._get_calendar_service(user_id, db)

        # Validate required fields for timed events
        if event_data.start_time is None or event_data.end_time is None:
            raise ValueError("start_time and end_time are required for creating events")

        # Prepare timezone-aware datetimes
        tz = pytz.timezone(self.timezone)

        # Ensure start_time is timezone-aware
        if event_data.start_time.tzinfo is None:
            # If naive, assume it's in Europe/Kiev timezone
            start_time = tz.localize(event_data.start_time)
        else:
            # If already timezone-aware, convert to Europe/Kiev
            start_time = event_data.start_time.astimezone(tz)

        # Ensure end_time is timezone-aware
        if event_data.end_time.tzinfo is None:
            # If naive, assume it's in Europe/Kiev timezone
            end_time = tz.localize(event_data.end_time)
        else:
            # If already timezone-aware, convert to Europe/Kiev
            end_time = event_data.end_time.astimezone(tz)

        # Construct event body for Google Calendar API
        event_body = {
            "summary": event_data.summary,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": self.timezone,
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": self.timezone,
            },
        }

        # Add optional description
        if event_data.description:
            event_body["description"] = event_data.description

        # Create the event
        try:
            created_event = await asyncio.to_thread(
                lambda: (
                    service.events()
                    .insert(calendarId="primary", body=event_body)
                    .execute()
                )
            )

            return {
                "summary": created_event.get("summary"),
                "start_time": self._parse_datetime(
                    created_event.get("start", {}).get("dateTime")
                ),
                "end_time": self._parse_datetime(
                    created_event.get("end", {}).get("dateTime")
                ),
                "html_link": created_event.get("htmlLink"),
                "description": created_event.get("description"),
            }

        except RefreshError as e:
            raise RefreshError(
                f"Failed to refresh access token for user {user_id}. "
                "The refresh token may be expired or revoked. "
                "Please re-authorize the application."
            ) from e
        except HttpError as e:
            raise HttpError(
                resp=e.resp,
                content=e.content,
                uri=e.uri,
            ) from e
        except Exception as e:
            raise Exception(f"Failed to create calendar event: {str(e)}") from e


google_calendar_service_instance = GoogleCalendarService()


def google_calendar_service() -> GoogleCalendarService:
    return google_calendar_service_instance
