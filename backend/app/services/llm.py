import datetime
import logging
from typing import TYPE_CHECKING

import pytz
from google import genai
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.google_calendar import GoogleCalendarService
from app.services.weather import WeatherService

if TYPE_CHECKING:
    from app.models.chat import ChatHistory

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        """
        Initialize the LLMService by validating required settings and creating the Google GenAI client.
        
        Validates that GOOGLE_API_KEY and GOOGLE_MODEL_NAME are configured in settings; if valid, constructs a genai.Client stored on self.client and stores the model name on self.model.
        
        Raises:
            ValueError: If GOOGLE_API_KEY or GOOGLE_MODEL_NAME is not set.
        
        Attributes:
            client: genai.Client instance created with GOOGLE_API_KEY.
            model: Name of the Google model from GOOGLE_MODEL_NAME.
        """
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
            Retrieve a human-readable summary of the current weather for a given city.
            
            Parameters:
                city (str): Name of the city to query (e.g., "Kyiv", "New York"). May include country or region to disambiguate.
            
            Returns:
                str: On success, a formatted summary containing city, weather description, temperature in Celsius, humidity percentage, and wind speed in m/s. On failure, an error message string describing the inability to fetch weather data.
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
            except Exception as e:
                logger.error(f"Weather API error for {city}: {e}")
                return f"Unable to fetch weather data for {city}. Error: {str(e)}"

        async def get_calendar_events(days: int = 7) -> str:
            """
            Retrieve and format the authenticated user's upcoming calendar events.
            
            Parameters:
                days (int): Number of days to look ahead for events (e.g., 1 for today, 7 for this week, 30 for this month). Defaults to 7.
            
            Returns:
                str: A human-readable list of upcoming events for the next `days` days. Each entry is numbered and includes the event title, start time (or "All day" if no start time), optional location, and a truncated description. If no events are found or an error occurs, returns a descriptive message.
            """
            try:
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

            except Exception as e:
                logger.error(f"Calendar API error for user {user_id}: {e}")
                return f"Unable to fetch calendar events. Error: {str(e)}"

        try:
            mapped_history = self._map_history_to_gemini(history_records)

            config = self._build_config_with_tools(
                [
                    get_current_weather,
                    get_calendar_events,
                ]
            )

            contents = [*mapped_history, user_text]

            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )

            self._log_token_usage(response)

            return response.text

        except Exception as e:
            logger.error(
                f"Gemini API error: {e}",
                extra={"json_fields": {"event": "llm_error", "error": str(e)}},
            )
            raise

    def _build_config_with_tools(self, tools: list) -> types.GenerateContentConfig:
        """
        Create a GenerateContentConfig that embeds a dynamic system instruction and the provided tool functions.
        
        The system instruction includes the current date and time (Europe/Kiev) and a default user location hint. This config is intended for model interactions that may invoke the provided async tool functions.
        
        Parameters:
            tools (list): A list of async Python callables exposed to the model for automatic function-calling.
        
        Returns:
            types.GenerateContentConfig: A config object containing the assembled system instruction and the provided tools.
        """
        tz = pytz.timezone("Europe/Kiev")
        now = datetime.datetime.now(tz)
        current_time_str = now.strftime("%Y-%m-%d %H:%M (%A)")

        dynamic_system_instruction = (
            f"{settings.SYSTEM_INSTRUCTION}\n"
            f"Current Date and Time: {current_time_str}.\n"
            f"User's Location: Ukraine (default for weather)."
        )

        return types.GenerateContentConfig(
            system_instruction=dynamic_system_instruction,
            tools=tools,
        )

    def _map_history_to_gemini(
        self, history_records: list["ChatHistory"]
    ) -> list[types.Content]:
        """
        Convert chat history records into Gemini Content objects.
        
        Each ChatHistory record is converted to a types.Content with the role taken from record.role
        and a single Part containing record.content.
        
        Parameters:
            history_records (list[ChatHistory]): Database chat history records to convert.
        
        Returns:
            list[types.Content]: Gemini Content objects corresponding to the input records.
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