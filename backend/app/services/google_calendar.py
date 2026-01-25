"""Google Calendar service for fetching user events."""

import asyncio
from datetime import datetime, time

from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.crud_user import user as crud_user


class GoogleCalendarService:
    """Service for interacting with Google Calendar API."""

    def __init__(self) -> None:
        """Initialize the Google Calendar Service."""
        self.token_uri = "https://oauth2.googleapis.com/token"

    async def get_today_events(self, user_id: int, db: AsyncSession) -> list[str]:
        """
        Fetch today's calendar events for a specific user.

        Args:
            user_id: The ID of the user whose events to fetch
            db: Database session

        Returns:
            List of formatted event strings (e.g., "10:00 - 11:00: Meeting with Team")

        Raises:
            ValueError: If user not found or no refresh token available
            RefreshError: If the refresh token is expired or revoked
            HttpError: If there's an error communicating with Google Calendar API
        """
        # 1. Fetch the user from DB
        user = await crud_user.get(db, id=user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        if not user.google_refresh_token:
            raise ValueError(
                f"User {user_id} has not authorized Google Calendar access. "
                "Please complete OAuth flow first."
            )

        # 2. Reconstruct Credentials
        try:
            credentials = Credentials(
                token=None,  # We don't have an access token, will be refreshed automatically
                refresh_token=user.google_refresh_token,
                token_uri=self.token_uri,
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET.get_secret_value(),
            )
        except Exception as e:
            raise ValueError(f"Failed to create credentials: {str(e)}") from e

        # 3. Build Service
        try:
            # Run the synchronous build() call in a thread pool
            service = await asyncio.to_thread(
                build, "calendar", "v3", credentials=credentials
            )
        except Exception as e:
            raise ValueError(f"Failed to build calendar service: {str(e)}") from e

        # 4. Query Events
        try:
            # Calculate timeMin (start of today in UTC)
            # Note: Using UTC for now. In the future, we can use user.timezone
            now = datetime.utcnow()
            time_min = datetime.combine(now.date(), time.min).isoformat() + "Z"
            time_max = datetime.combine(now.date(), time.max).isoformat() + "Z"

            # Call the Calendar API in a thread pool to avoid blocking
            events_result = await asyncio.to_thread(
                lambda: service.events()
                .list(
                    calendarId="primary",
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])

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

        # 5. Format Output
        formatted_events = []
        for event in events:
            # Get event start time
            start = event.get("start", {})
            end = event.get("end", {})
            summary = event.get("summary", "No Title")

            # Handle all-day events (date instead of dateTime)
            if "date" in start:
                formatted_events.append(f"All day: {summary}")
            else:
                # Parse dateTime for timed events
                start_dt = self._parse_datetime(start.get("dateTime"))
                end_dt = self._parse_datetime(end.get("dateTime"))

                if start_dt and end_dt:
                    start_time = start_dt.strftime("%H:%M")
                    end_time = end_dt.strftime("%H:%M")
                    formatted_events.append(f"{start_time} - {end_time}: {summary}")
                elif start_dt:
                    start_time = start_dt.strftime("%H:%M")
                    formatted_events.append(f"{start_time}: {summary}")
                else:
                    formatted_events.append(summary)

        return formatted_events

    def _parse_datetime(self, dt_string: str | None) -> datetime | None:
        """
        Parse ISO 8601 datetime string.

        Args:
            dt_string: ISO 8601 formatted datetime string

        Returns:
            Parsed datetime object or None if parsing fails
        """
        if not dt_string:
            return None

        try:
            # Handle timezone-aware datetime strings
            # Google Calendar API returns RFC3339 format
            if "T" in dt_string:
                # Remove timezone suffix for parsing (Z or +00:00)
                if dt_string.endswith("Z"):
                    dt_string = dt_string[:-1]
                elif "+" in dt_string or dt_string.count("-") > 2:
                    # Remove timezone offset
                    dt_string = dt_string.rsplit("+", 1)[0].rsplit("-", 1)[0]

                return datetime.fromisoformat(dt_string)
        except (ValueError, AttributeError):
            return None

        return None


# Singleton instance
google_calendar_service = GoogleCalendarService()
