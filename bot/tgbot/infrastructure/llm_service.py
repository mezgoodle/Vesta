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
        want_voice: bool = False,
    ) -> dict[str, Any]:
        """

        Process prompt.

        """

        endpoint = "/chat/process"

        status, data = await self._post(
            endpoint, {"user_id": user_id, "session_id": session_id, "message": prompt, "want_voice": want_voice}
        )

        if status == 200:
            return data
        else:
            return {}

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

    async def update_session(self, session_id: int, data: dict) -> bool:
        """
        Update session.
        """

        endpoint = f"/sessions/{session_id}"

        status, _ = await self._patch(endpoint, data)

        if status == 200:
            return True
        else:
            return False

    async def delete_session(self, session_id: int) -> bool:
        """
        Delete session.
        """

        endpoint = f"/sessions/{session_id}"

        status, _ = await self._delete(endpoint)

        if status == 200:
            return True
        else:
            return False


llm_service = LLMService()
