from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from tgbot.services.user_cache import UserCache


class ACLMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_cache: UserCache | None = data.get("user_cache")
        if not user_cache:
            return await handler(event, data)

        if not isinstance(event, Message):
            return await handler(event, data)
        message_text = event.text

        if message_text == "/start":
            return await handler(event, data)

        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        if user_cache.is_allowed(user.id):
            return await handler(event, data)
        return
