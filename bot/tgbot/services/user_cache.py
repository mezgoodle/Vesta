from typing import Iterable, Set


class UserCache:
    def __init__(self):
        self._allowed_ids: Set[int] = set()

    def load(self, user_ids: Iterable[int]):
        self._allowed_ids.update(user_ids)

    def add(self, user_id: int):
        self._allowed_ids.add(user_id)

    def is_allowed(self, user_id: int) -> bool:
        return user_id in self._allowed_ids

    def __repr__(self):
        return f"<UserCache count={len(self._allowed_ids)}>"
