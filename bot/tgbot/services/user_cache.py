from typing import Iterable


class UserCache:
    """Cache for mapping Telegram IDs to database user IDs."""

    def __init__(self):
        """Initialize the User Cache."""
        self._allowed_ids: dict[int, int] = {}

    def load(self, user_ids: Iterable[dict]) -> None:
        """
        Load users into the cache from a list of user dictionaries.

        Args:
            user_ids: Iterable of user dictionaries containing 'telegram_id' and 'id'
        """
        for u in user_ids:
            telegram_id = u.get("telegram_id")
            user_id = u.get("id")
            if telegram_id is not None and user_id is not None:
                self._allowed_ids[telegram_id] = user_id

    def add(self, user_id: int, telegram_id: int) -> None:
        """
        Add a user to the cache.

        Args:
            user_id: The database ID of the user
            telegram_id: The Telegram ID of the user
        """
        self._allowed_ids[telegram_id] = user_id

    def is_allowed(self, telegram_id: int) -> bool:
        """
        Check if a Telegram ID is in the cache.

        Args:
            telegram_id: The Telegram ID to check

        Returns:
            True if the user is in the cache, False otherwise
        """
        return telegram_id in self._allowed_ids

    def get_user_id_in_db(self, telegram_id: int) -> int | None:
        """
        Get the database user ID for a Telegram ID.

        Args:
            telegram_id: The Telegram ID to look up

        Returns:
            The database user ID, or None if not found
        """
        return self._allowed_ids.get(telegram_id)

    def __repr__(self):
        return f"<UserCache count={len(self._allowed_ids)}>"
