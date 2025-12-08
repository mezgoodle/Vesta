from typing import Optional

from tgbot.infrastructure.base_service import BaseAPIService


class UserService(BaseAPIService):
    """Service for weather forecast operations."""

    def __init__(self, base_url: Optional[str] = None, timeout: int = 10):
        """
        Initialize the forecast service.

        Args:
            base_url: Base URL of the backend API. If not provided, uses config.
            timeout: Request timeout in seconds.
        """
        super().__init__(base_url, timeout)

    async def get_approved_users(self) -> list[int]:
        """
        Get list of approved users.
        """
        endpoint = "/allowed/telegram-ids"

        status, data = await self._get(endpoint)

        if status == 200:
            return data
        else:
            return self._handle_error_response(
                status, data, "getting list of approved users"
            )

    async def update_user_approval(self, user_id: int, permissions: dict) -> str:
        """
        Update user permissions.

        Args:
            user_id: ID of the user to update permissions for.
            permissions: Dictionary of permissions to update.
        """
        endpoint = f"/telegram/{user_id}/approval"

        status, data = await self._patch(endpoint, permissions)

        if status == 200:
            return f"✅ User '{user_id}' approved."
        elif status == 404:
            return f"❌ User '{user_id}' not found. Please check the spelling."
        else:
            return self._handle_error_response(
                status, data, f"updating user approval for {user_id}"
            )


user_service = UserService()
