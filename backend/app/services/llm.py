import logging
from typing import TYPE_CHECKING

from google import genai
from google.genai import types

from app.core.config import settings

if TYPE_CHECKING:
    from app.models.chat import ChatHistory

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.model = settings.GOOGLE_MODEL_NAME

    async def chat(self, user_text: str, history_records: list["ChatHistory"]) -> str:
        """
        Send a chat message to Gemini with conversation history.

        Args:
            user_text: The user's message
            history_records: List of ChatHistory DB records (oldest to newest)

        Returns:
            The assistant's response text

        Raises:
            Exception: If the API call fails
        """
        try:
            # Map DB history to Gemini format
            mapped_history = self._map_history_to_gemini(history_records)

            # Create chat session with history
            chat = self.client.chats.create(
                model=self.model,
                config=types.GenerateContentConfig(
                    system_instruction=settings.SYSTEM_INSTRUCTION
                ),
                history=mapped_history,
            )

            # Send user message and get response
            response = chat.send_message(user_text)

            # Log token usage for GCP metrics
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

    async def close(self):
        """Close the Gemini client connection."""
        if self.client:
            await self.client.close()


async def llm_service():
    service = LLMService()
    try:
        yield service
    finally:
        await service.close()
