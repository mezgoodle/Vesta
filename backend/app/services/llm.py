import datetime
import logging
from typing import TYPE_CHECKING

import pytz
from google import genai
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas.calendar import CalendarEventCreate
from app.services.google_calendar import GoogleCalendarService
from app.services.weather import WeatherService

if TYPE_CHECKING:
    from app.models.chat import ChatHistory

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not set")
        if not settings.GOOGLE_MODEL_NAME:
            raise ValueError("GOOGLE_MODEL_NAME is not set")

        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.model = settings.GOOGLE_MODEL_NAME

    async def chat(
        self,
        user_text: str,
        history_records: list["ChatHistory"],
        user_id: int,
        db: AsyncSession,
    ) -> str:
        """
        Send a chat message to Gemini with automatic function calling support.

        Args:
            user_text: The user's message
            history_records: List of ChatHistory DB records (oldest to newest)
            user_id: The authenticated user's ID (for calendar access)
            db: Database session (for calendar access)

        Returns:
            The assistant's response text

        Raises:
            Exception: If the API call fails
        """

        async def get_current_weather(city: str) -> str:
            """
            Get the current weather information for a specified city.

            Use this function when the user asks about weather conditions, temperature,
            humidity, wind speed, or general climate in a specific location.

            Args:
                city: The name of the city to get weather for (e.g., 'London', 'New York', 'Tokyo', 'Kyiv')

            Returns:
                A formatted string with weather information including temperature in Celsius,
                weather description, humidity percentage, and wind speed in m/s.
            """
            try:
                weather_service = WeatherService()
                try:
                    weather_data = (
                        await weather_service.get_current_weather_by_city_name(
                            city=city
                        )
                    )
                    return (
                        f"Weather in {weather_data.city}: "
                        f"{weather_data.description}, "
                        f"Temperature: {weather_data.temp}°C, "
                        f"Humidity: {weather_data.humidity}%, "
                        f"Wind Speed: {weather_data.wind_speed} m/s"
                    )
                finally:
                    await weather_service.close()
            except Exception:
                logger.error(f"Weather API error for {city}")
                return f"Unable to fetch weather data for {city}."

        async def get_calendar_events(days: int = 7) -> str:
            """
            Get upcoming calendar events for the authenticated user.

            Use this function when the user asks about their schedule, meetings,
            appointments, or what's on their calendar.

            Args:
                days: Number of days to look ahead for events. Default is 7 days.
                     Use 1 for today, 7 for this week, 30 for this month.

            Returns:
                A formatted string listing upcoming calendar events with their titles,
                start times, end times, and locations (if available). Returns a message
                if no events are found.
            """
            try:
                days = max(1, min(days, 30))
                calendar_service = GoogleCalendarService()
                events = await calendar_service.get_upcoming_events(
                    user_id=user_id,
                    db=db,
                    days=days,
                )

                if not events:
                    return f"No events found in the next {days} days."

                result = f"Upcoming events (next {days} days):\n"
                for i, event in enumerate(events, 1):
                    if event.start_time:
                        start = event.start_time.strftime("%Y-%m-%d %H:%M")
                    else:
                        start = "All day"

                    result += f"{i}. {event.summary} - {start}"

                    if event.location:
                        result += f" at {event.location}"

                    if event.description:
                        desc = (
                            event.description[:100] + "..."
                            if len(event.description) > 100
                            else event.description
                        )
                        result += f" ({desc})"

                    result += "\n"

                return result.strip()

            except Exception:
                logger.error(f"Calendar API error for user {user_id}")
                return "Unable to fetch calendar events."

        async def schedule_event_tool(
            summary: str,
            start_time_iso: str,
            duration_minutes: int = 60,
            description: str = "",
        ) -> str:
            """
            Schedule a new event in the user's Google Calendar.

            Use this function when the user wants to create, schedule, or add an event
            to their calendar. This includes meetings, appointments, reminders, or any
            time-blocked activity.

            IMPORTANT: The start_time_iso parameter MUST include both date and time in
            ISO 8601 format. Examples:
            - '2026-02-15T14:00:00' (February 15, 2026 at 2:00 PM)
            - '2026-03-01T09:30:00' (March 1, 2026 at 9:30 AM)
            - '2026-12-25T18:00:00' (December 25, 2026 at 6:00 PM)

            The time will be interpreted in Europe/Kiev timezone.

            Args:
                summary: The title/name of the event (e.g., 'Team Meeting', 'Doctor Appointment')
                start_time_iso: Start date and time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS).
                               MUST include both date and time components.
                duration_minutes: Duration of the event in minutes. Default is 60 minutes (1 hour).
                                 Common values: 30 (half hour), 60 (1 hour), 90 (1.5 hours), 120 (2 hours)
                description: Optional description or notes for the event

            Returns:
                A success message with a link to the created event in Google Calendar,
                or an error message if the event could not be created.
            """
            try:
                # Parse the ISO datetime string
                try:
                    start_time = datetime.datetime.fromisoformat(start_time_iso)
                except ValueError as e:
                    return (
                        f"Invalid datetime format: {start_time_iso}. "
                        "Please use ISO 8601 format (YYYY-MM-DDTHH:MM:SS). "
                        f"Error: {str(e)}"
                    )

                # Calculate end_time from duration
                end_time = start_time + datetime.timedelta(minutes=duration_minutes)

                # Create event data
                event_data = CalendarEventCreate(
                    summary=summary,
                    start_time=start_time,
                    end_time=end_time,
                    description=description if description else None,
                )

                # Create the event
                calendar_service = GoogleCalendarService()
                created_event = await calendar_service.create_event(
                    user_id=user_id,
                    event_data=event_data,
                    db=db,
                )

                # Format response
                start_time = created_event.get("start_time")
                end_time = created_event.get("end_time")

                if start_time and end_time:
                    start_formatted = start_time.strftime("%B %d, %Y at %H:%M")
                    end_formatted = end_time.strftime("%H:%M")
                    time_info = f"📅 {start_formatted} - {end_formatted}\n"
                else:
                    time_info = ""

                return (
                    f"✅ Event '{summary}' successfully created!\n"
                    f"{time_info}"
                    f"🔗 View event: {created_event['html_link']}"
                )

            except Exception as e:
                logger.error(
                    f"Failed to create calendar event for user {user_id}: {str(e)}"
                )
                return f"Unable to create calendar event. Error: {str(e)}"

        try:
            mapped_history = self._map_history_to_gemini(history_records)

            config = self._build_config_with_tools(
                [
                    get_current_weather,
                    get_calendar_events,
                    schedule_event_tool,
                ]
            )

            contents = [
                *mapped_history,
                types.Content(role="user", parts=[types.Part(text=user_text)]),
            ]

            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )

            self._log_token_usage(response)

            if response.text:
                return response.text
            else:
                return "I couldn't generate a response. Please try again."

        except Exception:
            logger.error(
                "Gemini API error", extra={"json_fields": {"event": "llm_error"}}
            )
            raise

    def _build_config_with_tools(self, tools: list) -> types.GenerateContentConfig:
        """
        Build GenerateContentConfig with dynamic tools and system instruction.

        Args:
            tools: List of Python async functions to use as tools

        Returns:
            GenerateContentConfig with automatic function calling enabled
        """
        tz = pytz.timezone("Europe/Kiev")
        now = datetime.datetime.now(tz)
        current_time_str = now.strftime("%Y-%m-%d %H:%M (%A)")

        dynamic_system_instruction = (
            f"{settings.SYSTEM_INSTRUCTION}\n"
            f"Current Date and Time: {current_time_str}.\n"
            f"User's Location: Ukraine (default for weather).\n"
            f"--- TOOL GUIDELINES ---\n"
            f"1. Proactivity: If the user asks about 'today' or 'my day', proactively call BOTH `get_calendar_events(days=1)` and `get_current_weather` to provide a complete summary.\n"
            f"2. Weather Constraints: You can only fetch CURRENT weather. If the user asks for a forecast for a future date, inform them that you currently only have access to real-time weather data.\n"
            f"3. Scheduling: When using `schedule_event_tool`, always use the 'Current Date' above as a reference to calculate relative dates like 'tomorrow' or 'next Friday'.\n"
            f"4. Clarity: If the user's request is ambiguous (e.g., 'What's the weather?'), assume their current location (Ukraine) unless specified otherwise."
        )

        return types.GenerateContentConfig(
            system_instruction=dynamic_system_instruction,
            tools=tools,
        )

    def _map_history_to_gemini(
        self, history_records: list["ChatHistory"]
    ) -> list[types.Content]:
        """
        Convert DB chat history to Gemini Content format.

        Maps:
        - DB role "assistant" -> Gemini role "model"
        - DB role "user" -> Gemini role "user"

        Args:
            history_records: List of ChatHistory DB records

        Returns:
            List of Gemini Content objects
        """
        mapped_history = []
        for record in history_records:
            mapped_history.append(
                types.Content(
                    role=record.role,
                    parts=[types.Part(text=record.content)],
                )
            )
        return mapped_history

    def _log_token_usage(self, response) -> None:
        """
        Log token usage metrics for GCP monitoring.

        Args:
            response: The Gemini API response object
        """
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = response.usage_metadata
            logger.info(
                "LLM token usage",
                extra={
                    "json_fields": {
                        "event": "llm_usage",
                        "input_tokens": getattr(usage, "prompt_token_count", 0),
                        "output_tokens": getattr(usage, "candidates_token_count", 0),
                        "total_tokens": getattr(usage, "total_token_count", 0),
                    }
                },
            )

    def close(self):
        """Close the Gemini client connection."""
        if self.client:
            self.client.close()


async def llm_service():
    service = LLMService()
    try:
        yield service
    finally:
        service.close()
