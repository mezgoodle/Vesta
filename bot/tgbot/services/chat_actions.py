import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from aiogram import Bot

logger = logging.getLogger(__name__)


async def _keep_typing(bot: Bot, chat_id: int, interval: float = 4.0) -> None:
    """Send typing chat action periodically until cancelled."""
    while True:
        try:
            await bot.send_chat_action(chat_id=chat_id, action="typing")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.debug(f"Failed to send typing chat action to chat {chat_id}: {e}")

        try:
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            break


@asynccontextmanager
async def show_typing(
    bot: Bot, chat_id: int, interval: float = 4.0
) -> AsyncIterator[None]:
    """
    Context manager that keeps sending 'typing' chat action every `interval` seconds
    until the context exits.
    """
    task = asyncio.create_task(_keep_typing(bot, chat_id, interval))
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
