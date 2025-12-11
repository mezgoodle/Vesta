from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import CallbackQuery, Message
from cachetools import TTLCache

THROTTLE_TIME_OTHER = 1


class ThrottlingMiddleware(BaseMiddleware):
    caches = {
        "default": TTLCache(maxsize=10_000, ttl=THROTTLE_TIME_OTHER),
    }

    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        throttling_key = get_flag(
            handler=data, name="throttling_key", default="default"
        )
        if throttling_key is not None and throttling_key in self.caches:
            cache = self.caches[throttling_key]
            chat_id: int | None = None
            if isinstance(event, Message):
                chat_id = event.chat.id
            elif isinstance(event, CallbackQuery) and event.message:
                chat_id = event.message.chat.id

            if chat_id is not None:
                if chat_id in cache:
                    return
                cache[chat_id] = None
        return await handler(event, data)
