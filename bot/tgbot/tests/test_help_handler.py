import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

pytestmark = pytest.mark.asyncio

from tgbot.handlers.help import help_command


async def test_help_command_replies_with_supported_commands() -> None:
    message = AsyncMock()
    message.from_user = SimpleNamespace(username="tester")

    await help_command(message)

    message.reply.assert_awaited_once()
    reply_text = message.reply.await_args.args[0]
    assert "Conversation with AI" in reply_text
    assert "/weather" in reply_text
    assert "/upcoming" in reply_text
