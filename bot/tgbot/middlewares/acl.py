from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from tgbot.services.user_cache import UserCache


class ACLMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_cache: UserCache = data.get("user_cache")
        message_text = event.text

        if message_text == "/start":
            return await handler(event, data)

        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        if user_cache.is_allowed(user.id):
            return await handler(event, data)
        return
