from typing import Any

from tgbot.infrastructure.base_service import BaseAPIService


class LLMService(BaseAPIService):
    """Service for LLM operations."""

    def __init__(self, base_url: str | None = None, timeout: int = 10):
        super().__init__(base_url, timeout)

    async def process_prompt(
        self,
        prompt: str,
        user_id: int,
        session_id: int | None = None,
        session_title: str | None = None,
        want_voice: bool = False,
    ) -> tuple[dict[str, Any] | None, str | None]:
        """
        Process prompt.

        Returns:
            Tuple of (response_data, error_message).
            If successful, (data, None).
            If failed, (None, error_message).
        """
        endpoint = "/chat/process"

        status, data = await self._post(
            endpoint,
            {
                "user_id": user_id,
                "session_id": session_id,
                "message": prompt,
                "want_voice": want_voice,
                "session_title": session_title,
            },
            timeout=60,
        )

        if status == 200 and data:
            return data, None
        else:
            error_message = self._handle_error_response(
                status, data, "processing chat prompt"
            )
            return None, error_message

    async def get_sessions_by_user_id(self, user_id: int) -> list[dict]:
        """
        Get list of sessions for user.
        """
        endpoint = "/sessions"

        status, data = await self._get(endpoint, params={"user_id": user_id})

        if status == 200:
            return data
        else:
            return []

    async def update_session(self, session_id: int, data: dict) -> tuple[bool, str]:
        """
        Update session.

        Returns:
            Tuple of (success, message).
        """
        endpoint = f"/sessions/{session_id}"

        status, resp_data = await self._patch(endpoint, data)

        if status == 200:
            return True, "Session title changed."
        else:
            return False, self._handle_error_response(
                status, resp_data, f"updating session '{session_id}'"
            )

    async def delete_session(self, session_id: int) -> tuple[bool, str]:
        """
        Delete session.

        Returns:
            Tuple of (success, message).
        """
        endpoint = f"/sessions/{session_id}"

        status, resp_data = await self._delete(endpoint)

        if status == 200:
            return True, "Session deleted."
        else:
            return False, self._handle_error_response(
                status, resp_data, f"deleting session '{session_id}'"
            )


llm_service = LLMService()
