from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from tgbot.config import Settings


class IsAdminFilter(BaseFilter):
    def __init__(self):
        super().__init__()

    async def __call__(
        self, message: Message | CallbackQuery, config: Settings
    ) -> bool:
        return message.from_user.id in config.admins
