import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

pytestmark = pytest.mark.asyncio

from tgbot.handlers.echo import command_start_handler


async def test_start_handler_greets_allowed_user() -> None:
    message = AsyncMock()
    message.from_user = SimpleNamespace(id=100, full_name="Test User", username="tester")
    user_cache = AsyncMock()
    user_cache.is_allowed.return_value = True
    config = SimpleNamespace(admins=[42])

    await command_start_handler(message, user_cache, config)

    message.answer.assert_awaited_once()
    user_cache.is_allowed.assert_called_once_with(100)


async def test_start_handler_notifies_admin_for_new_user(monkeypatch) -> None:
    message = AsyncMock()
    message.from_user = SimpleNamespace(id=100, full_name="Test User", username="tester")
    user_cache = AsyncMock()
    user_cache.is_allowed.return_value = False
    config = SimpleNamespace(admins=[42])
    send_message_mock = AsyncMock()

    monkeypatch.setattr("tgbot.handlers.echo.bot.send_message", send_message_mock)

    await command_start_handler(message, user_cache, config)

    message.answer.assert_awaited_once_with(
        "You are not allowed to use this bot. Permission request has been sent to the administrator."
    )
    send_message_mock.assert_awaited_once()
    assert send_message_mock.await_args.kwargs["chat_id"] == 42
