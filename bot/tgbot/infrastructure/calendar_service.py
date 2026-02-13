from datetime import datetime

from aiogram.utils.formatting import Bold, Underline
from aiogram.utils.markdown import hbold

from tgbot.infrastructure.base_service import BaseAPIService


class CalendarService(BaseAPIService):
    """Service for calendar operations."""

    def __init__(self, base_url: str | None = None, timeout: int = 10):
        """
        Initialize the calendar service.

        Args:
            base_url: Base URL of the backend API. If not provided, uses config.
            timeout: Request timeout in seconds.
        """
        super().__init__(base_url, timeout)

    async def get_today_events(self, user_id: int) -> str:
        """
        Fetch today's calendar events.

        Args:
            user_id: User ID to fetch events for.

        Returns:
            Formatted calendar events information as a string.
        """
        endpoint = "/api/v1/calendar/events/today"
        params = {"user_id": user_id}

        status, data = await self._get(endpoint, params)

        # Handle different response scenarios
        if status == 200:
            return self._format_calendar_data(data, "Today's Events")
        elif status == 404:
            return "❌ No events found for today."
        else:
            return self._handle_error_response(status, data, "fetching today's events")

    async def get_upcoming_events(self, user_id: int, days: int = 7) -> str:
        """
        Fetch upcoming calendar events.

        Args:
            user_id: User ID to fetch events for.
            days: Number of days to fetch events for.

        Returns:
            Formatted calendar events information as a string.
        """
        endpoint = "/api/v1/calendar/events/upcoming"
        params = {"user_id": user_id, "days": days}

        status, data = await self._get(endpoint, params)

        # Handle different response scenarios
        if status == 200:
            return self._format_calendar_data(data, "Upcoming Events")
        elif status == 404:
            return "❌ No upcoming events found."
        else:
            return self._handle_error_response(status, data, "fetching upcoming events")

    def _format_calendar_data(self, data: dict, title: str) -> str:
        """
        Format calendar events data into a user-friendly message.

        Args:
            data: Dictionary containing 'events' list and 'count'.

        Returns:
            Formatted string with calendar events.
        """
        try:
            events = data.get("events", [])
            count = data.get("count", 0)

            if count == 0 or not events:
                return f"📅 No events scheduled for {title.lower()}."

            # Build the header
            header = f"📅 {hbold(title)} ({count} event{'s' if count != 1 else ''})\n\n"

            # Format each event
            event_messages = []
            for idx, event in enumerate(events, 1):
                summary = event.get("summary", "Untitled Event")
                start_time = event.get("start_time", "")
                end_time = event.get("end_time", "")
                is_all_day = event.get("is_all_day", False)
                description = event.get("description", "")
                location = event.get("location", "")

                # Format event message
                event_msg = f"{hbold(idx)}. {Underline(Bold(summary)).as_html()}\n"

                # Add time information
                if is_all_day:
                    # For all-day events, show the date
                    if start_time:
                        try:
                            start_dt = datetime.fromisoformat(
                                start_time.replace("Z", "+00:00")
                            )
                            event_msg += (
                                f"🕐 All day - {start_dt.strftime('%A, %B %d')}\n"
                            )
                        except Exception:
                            event_msg += "🕐 All day event\n"
                    else:
                        event_msg += "🕐 All day event\n"
                else:
                    # Extract time from ISO format (e.g., "2026-02-11T14:53:39.927Z")
                    if start_time and end_time:
                        try:
                            start_dt = datetime.fromisoformat(
                                start_time.replace("Z", "+00:00")
                            )
                            end_dt = datetime.fromisoformat(
                                end_time.replace("Z", "+00:00")
                            )
                            # Format: "Wednesday, February 11 • 14:30 - 15:45"
                            date_str = start_dt.strftime("%A, %B %d")
                            time_str = f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
                            event_msg += f"🕐 {date_str} • {time_str}\n"
                        except Exception:
                            event_msg += f"🕐 {start_time} - {end_time}\n"

                # Add location if available
                if location:
                    event_msg += f"📍 {location}\n"

                # Add description if available
                if description:
                    # Truncate long descriptions
                    desc_preview = (
                        description[:100] + "..."
                        if len(description) > 100
                        else description
                    )
                    event_msg += f"📝 {desc_preview}\n"

                event_messages.append(event_msg)

            # Combine all parts
            return header + "\n".join(event_messages)

        except Exception as e:
            self.logger.error(f"Error formatting calendar data: {e}")
            return "❌ Error formatting calendar events."


calendar_service = CalendarService()
