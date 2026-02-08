from aiogram.filters import BaseFilter
from aiogram.types import Message

from tgbot.services.user_cache import UserCache


class IsApprovedUserFilter(BaseFilter):
    def __init__(self):
        super().__init__()

    async def __call__(self, message: Message, user_cache: UserCache) -> bool:
        return user_cache.is_allowed(message.from_user.id)
