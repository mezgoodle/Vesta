from tgbot.infrastructure.base_service import BaseAPIService


class UserService(BaseAPIService):
    """Service for weather forecast operations."""

    def __init__(self, base_url: str | None = None, timeout: int = 10):
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
        endpoint = "/api/v1/users/allowed/telegram-ids"

        status, data = await self._get(endpoint)

        if status == 200:
            return data
        else:
            return []

    async def update_user_approval(
        self,
        user_id: int,
        permissions: dict,
        full_name: str | None = None,
        username: str | None = None,
    ) -> tuple[dict | None, str]:
        """
        Update user permissions.

        Args:
            user_id: ID of the user to update permissions for.
            permissions: Dictionary of permissions to update.
        """
        endpoint = f"/api/v1/users/telegram/{user_id}/approval"

        status, data = await self._patch(endpoint, permissions)

        if status == 200:
            return data, f"✅ User '{user_id}' approved."
        elif status == 404:
            user_data = {
                "telegram_id": user_id,
                "full_name": full_name,
                "username": username,
                "is_allowed": True,
            }
            data, _ = await self.create_user(user_data)
            if data:
                return (
                    data,
                    f"✅ User '{user_id}' created. If you want to change permissions, text @sylvenis.",
                )
            else:
                return None, self._handle_error_response(
                    status, data, f"creating user '{user_id}'"
                )
        else:
            return None, self._handle_error_response(
                status, data, f"updating user approval for {user_id}"
            )

    async def get_user_by_telegram_id(self, telegram_id: int) -> dict | None:
        """
        Get user by telegram id.
        """
        endpoint = f"/api/v1/users/telegram/{telegram_id}"

        status, data = await self._get(endpoint)

        if status == 200:
            return data
        else:
            return None

    async def create_user(self, user_data: dict) -> tuple[dict | None, str]:
        """
        Create a new user.

        Args:
            user_data: Dictionary of user data to create.
        """
        endpoint = "/api/v1/users"

        status, data = await self._post(endpoint, user_data)

        if status == 201:
            return data, f"✅ User '{user_data['telegram_id']}' created."
        else:
            return None, self._handle_error_response(
                status, data, f"creating user '{user_data['telegram_id']}'"
            )

    async def start_google_auth(self, user_id: int) -> tuple[dict | None, str]:
        """
        Start Google authentication.

        Args:
            user_id: ID of the user to start authentication for.
        """
        endpoint = "/api/v1/google-auth/login"

        status, data = await self._get(endpoint, params={"user_id": user_id})

        if status == 200:
            return data, f"✅ Google authentication started for user '{user_id}'."
        else:
            return None, self._handle_error_response(
                status, data, f"starting google authentication for user '{user_id}'"
            )


user_service = UserService()
