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
            if isinstance(event, Message):
                if event.chat.id in self.caches[throttling_key]:
                    return
                elif "chat" in event:
                    self.caches[throttling_key][event.chat.id] = None
            elif isinstance(event, CallbackQuery):
                if event.message.chat.id in self.caches[throttling_key]:
                    return
                elif "chat" in event.message:
                    self.caches[throttling_key][event.message.chat.id] = None
        return await handler(event, data)
