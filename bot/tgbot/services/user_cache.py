from typing import Iterable


class UserCache:
    def __init__(self):
        self._allowed_ids: dict[int, int] = {}

    def load(self, user_ids: Iterable[dict]) -> None:
        for u in user_ids:
            telegram_id = u.get("telegram_id")
            user_id = u.get("id")
            if telegram_id is not None and user_id is not None:
                self._allowed_ids[telegram_id] = user_id

    def add(self, user_id: int, telegram_id: int) -> None:
        self._allowed_ids[telegram_id] = user_id

    def is_allowed(self, telegram_id: int) -> bool:
        return telegram_id in self._allowed_ids

    def get_user_id_in_db(self, telegram_id: int) -> int | None:
        return self._allowed_ids.get(telegram_id)

    def __repr__(self):
        return f"<UserCache count={len(self._allowed_ids)}>"
