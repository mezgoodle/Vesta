import datetime
import logging
from typing import TYPE_CHECKING, Any

import pytz
from google import genai
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services import llm_tools
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

        # Define available tools for function calling
        self.tools = [
            llm_tools.get_current_weather,
            llm_tools.get_calendar_events,
        ]

    def _build_config(self) -> types.GenerateContentConfig:
        """
        Build GenerateContentConfig with tools and function calling enabled.
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
        )

    async def chat(
        self,
        user_text: str,
        history_records: list["ChatHistory"],
        user_id: int,
        db: AsyncSession,
    ) -> str:
        """
        Send a chat message to Gemini with conversation history and function calling support.

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
        try:
            # Map DB history to Gemini format
            mapped_history = self._map_history_to_gemini(history_records)

            # Create chat session with history and tools
            chat = self.client.aio.chats.create(
                model=self.model,
                config=self._build_config(),
                history=mapped_history,
                tools=self.tools,
            )

            # Send user message and get response
            response = await chat.send_message(user_text)

            # Function calling execution loop
            max_iterations = 5  # Prevent infinite loops
            iteration = 0

            while iteration < max_iterations:
                iteration += 1

                # Check if response contains function calls
                function_call_detected = False

                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        # Check if this part is a function call
                        if hasattr(part, "function_call") and part.function_call:
                            function_call_detected = True
                            function_call = part.function_call

                            logger.info(
                                f"Function call detected: {function_call.name}",
                                extra={
                                    "json_fields": {
                                        "event": "function_call",
                                        "function_name": function_call.name,
                                        "args": dict(function_call.args),
                                    }
                                },
                            )

                            # Execute the function
                            result = await self._execute_function(
                                function_call, user_id, db
                            )

                            # Send function result back to Gemini
                            response = await chat.send_message(
                                types.Part.from_function_response(
                                    name=function_call.name,
                                    response=result,
                                )
                            )
                            break  # Process one function call at a time

                # If no function call detected, we have the final text response
                if not function_call_detected:
                    break

            # Log token usage for GCP metrics (accumulated across all turns)
            self._log_token_usage(response)

            return response.text

        except Exception as e:
            logger.error(
                f"Gemini API error: {e}",
                extra={"json_fields": {"event": "llm_error", "error": str(e)}},
            )
            raise

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
            # Map assistant role to model for Gemini
            gemini_role = "model" if record.role == "assistant" else record.role

            mapped_history.append(
                types.Content(
                    role=gemini_role,
                    parts=[types.Part(text=record.content)],
                )
            )
        return mapped_history

    async def _execute_function(
        self, function_call: Any, user_id: int, db: AsyncSession
    ) -> dict[str, Any]:
        """
        Execute the requested function and return result.

        Args:
            function_call: The function call object from Gemini
            user_id: The authenticated user's ID
            db: Database session

        Returns:
            Dictionary containing the function result or error
        """
        function_name = function_call.name
        args = dict(function_call.args)

        try:
            if function_name == "get_current_weather":
                weather_service = WeatherService()
                try:
                    city = args.get("city", "")
                    weather_data = (
                        await weather_service.get_current_weather_by_city_name(
                            city=city
                        )
                    )
                    return weather_data.model_dump()
                finally:
                    await weather_service.close()

            elif function_name == "get_calendar_events":
                calendar_service = GoogleCalendarService()
                days = args.get("days", 7)
                events = await calendar_service.get_upcoming_events(
                    user_id=user_id,
                    db=db,
                    days=days,
                )
                return {
                    "events": [event.model_dump() for event in events],
                    "count": len(events),
                }

            else:
                return {"error": f"Unknown function: {function_name}"}

        except Exception as e:
            logger.error(
                f"Function execution error: {function_name} - {e}",
                extra={
                    "json_fields": {
                        "event": "function_execution_error",
                        "function_name": function_name,
                        "error": str(e),
                    }
                },
            )
            # Return error to LLM so it can inform the user politely
            return {"error": str(e)}

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
