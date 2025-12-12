import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject


class LoggingMiddleware(BaseMiddleware):
    """
    Middleware to log all incoming messages and callbacks with structured data.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Log messages
        if isinstance(event, Message):
            user = event.from_user
            extra = {
                "user_id": user.id if user else None,
                "username": user.username if user else None,
                "chat_id": event.chat.id,
                "message_type": "message",
                "text": event.text or event.caption or "[media]",
            }

            logging.info(
                f"Message from user_id={extra['user_id']} username={extra['username']} "
                f"chat_id={extra['chat_id']}: {extra['text'][:100]}",
                extra={"json_payload": extra},
            )

        # Log callback queries
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            extra = {
                "user_id": user.id if user else None,
                "username": user.username if user else None,
                "chat_id": event.message.chat.id if event.message else None,
                "message_type": "callback",
                "callback_data": event.data,
            }

            logging.info(
                f"Callback from user_id={extra['user_id']} username={extra['username']} "
                f"chat_id={extra['chat_id']}: {extra['callback_data']}",
                extra={"json_payload": extra},
            )

        return await handler(event, data)
