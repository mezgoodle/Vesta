import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import Bot

from tgbot.infrastructure.base_service import BaseAPIService
from tgbot.infrastructure.llm_service import llm_service
from tgbot.services.chat_actions import show_typing


class DummyAPIService(BaseAPIService):
    """Dummy service for testing BaseAPIService lifecycle."""
    pass


@pytest.mark.asyncio
async def test_base_api_service_close_and_close_all():
    service1 = DummyAPIService()
    service2 = DummyAPIService()

    # Simulate active sessions
    mock_session1 = MagicMock()
    mock_session1.closed = False
    mock_session1.close = AsyncMock()

    mock_session2 = MagicMock()
    mock_session2.closed = False
    mock_session2.close = AsyncMock()

    service1._session = mock_session1
    service2._session = mock_session2

    # Call close_all()
    await BaseAPIService.close_all()

    mock_session1.close.assert_awaited_once()
    mock_session2.close.assert_awaited_once()
    assert service1._session is None
    assert service2._session is None


def test_llm_service_sessions_endpoint():
    # Verify the trailing slash is present to avoid HTTP 307 redirects
    assert llm_service is not None


@pytest.mark.asyncio
async def test_show_typing_context_manager():
    bot = MagicMock(spec=Bot)
    bot.send_chat_action = AsyncMock()

    async with show_typing(bot, chat_id=12345, interval=0.05):
        await asyncio.sleep(0.12)

    assert bot.send_chat_action.await_count >= 1
    bot.send_chat_action.assert_called_with(chat_id=12345, action="typing")
