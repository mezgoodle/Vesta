from typing import Iterable


class UserCache:
    def __init__(self):
        self._allowed_ids: dict[int, int] = {}

    def load(self, user_ids: Iterable[dict]) -> None:
        for u in user_ids:
            self._allowed_ids[u["telegram_id"]] = u["id"]

    def add(self, user_id: int, telegram_id: int) -> None:
        self._allowed_ids[telegram_id] = user_id

    def is_allowed(self, telegram_id: int) -> bool:
        return telegram_id in self._allowed_ids

    def get_user_id_in_db(self, telegram_id: int) -> int | None:
        return self._allowed_ids.get(telegram_id)

    def __repr__(self):
        return f"<UserCache count={len(self._allowed_ids)}>"
