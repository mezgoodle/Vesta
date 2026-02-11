from aiogram.filters import BaseFilter
from aiogram.types import Message

from tgbot.services.user_cache import UserCache


class IsApprovedUserFilter(BaseFilter):
    def __init__(self):
        super().__init__()

    async def __call__(
        self, message: Message, user_cache: UserCache
    ) -> bool | dict[str, int]:
        if user_cache.is_allowed(message.from_user.id) and (
            user_db_id := user_cache.get_user_id_in_db(message.from_user.id)
        ):
            return {"user_db_id": user_db_id}
        return False
