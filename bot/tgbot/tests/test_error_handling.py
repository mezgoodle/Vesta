import os
from unittest.mock import AsyncMock, MagicMock

import pytest

# Ensure dummy env vars exist for Settings before importing tgbot modules
os.environ.setdefault("BOT_TOKEN", "1234567890:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
os.environ.setdefault("BACKEND_API_KEY", "dummy_key")

from tgbot.infrastructure.base_service import BaseAPIService
from tgbot.infrastructure.llm_service import llm_service
from tgbot.handlers.llm import _process_llm_request


class DummyService(BaseAPIService):
    """Test subclass of BaseAPIService."""
    pass


def test_base_api_service_handle_error_response_timeout():
    service = DummyService()
    msg = service._handle_error_response(0, {"detail": "Request timed out"}, "chat")
    assert "Request timed out" in msg
    assert "⏱️" in msg


def test_base_api_service_handle_error_response_offline():
    service = DummyService()
    msg = service._handle_error_response(0, None, "chat")
    assert "offline" in msg
    assert "❌" in msg


def test_base_api_service_handle_error_response_503_with_detail():
    service = DummyService()
    detail = "The AI service is experiencing high demand. Please try again in a moment."
    msg = service._handle_error_response(503, {"detail": detail}, "chat")
    assert detail in msg
    assert "⏳" in msg


def test_base_api_service_handle_error_response_503_fallback():
    service = DummyService()
    msg = service._handle_error_response(503, None, "chat")
    assert "high demand" in msg
    assert "⏳" in msg


def test_base_api_service_handle_error_response_429():
    service = DummyService()
    msg = service._handle_error_response(429, {"detail": "Too many requests."}, "chat")
    assert "Too many requests." in msg
    assert "⏳" in msg


def test_base_api_service_handle_error_response_500():
    service = DummyService()
    msg = service._handle_error_response(500, {"detail": "Failed to process chat message"}, "chat")
    assert "Server error: Failed to process chat message" in msg
    assert "❌" in msg


def test_base_api_service_handle_error_response_504():
    service = DummyService()
    msg = service._handle_error_response(504, None, "chat")
    assert "Request timed out" in msg


@pytest.mark.asyncio
async def test_llm_service_process_prompt_success(monkeypatch):
    expected_data = {"response": "Hello world", "session_id": 1}
    mock_post = AsyncMock(return_value=(200, expected_data))
    monkeypatch.setattr(llm_service, "_post", mock_post)

    data, error = await llm_service.process_prompt(
        prompt="Hi",
        user_id=1,
    )

    assert data == expected_data
    assert error is None


@pytest.mark.asyncio
async def test_llm_service_process_prompt_503(monkeypatch):
    mock_post = AsyncMock(
        return_value=(
            503,
            {"detail": "The AI service is experiencing high demand. Please try again in a moment."},
        )
    )
    monkeypatch.setattr(llm_service, "_post", mock_post)

    data, error = await llm_service.process_prompt(
        prompt="Hi",
        user_id=1,
    )

    assert data is None
    assert error is not None
    assert "high demand" in error


@pytest.mark.asyncio
async def test_llm_service_process_prompt_timeout(monkeypatch):
    mock_post = AsyncMock(return_value=(0, {"detail": "Request timed out"}))
    monkeypatch.setattr(llm_service, "_post", mock_post)

    data, error = await llm_service.process_prompt(
        prompt="Hi",
        user_id=1,
    )

    assert data is None
    assert error is not None
    assert "Request timed out" in error


@pytest.mark.asyncio
async def test_llm_service_session_methods(monkeypatch):
    monkeypatch.setattr(llm_service, "_patch", AsyncMock(return_value=(200, {})))
    monkeypatch.setattr(llm_service, "_delete", AsyncMock(return_value=(200, {})))

    ok, msg = await llm_service.update_session(1, {"title": "New Title"})
    assert ok is True
    assert "Session title changed" in msg

    ok, msg = await llm_service.delete_session(1)
    assert ok is True
    assert "Session deleted" in msg


@pytest.mark.asyncio
async def test_process_llm_request_handler_displays_error(monkeypatch):
    mock_post = AsyncMock(
        return_value=(
            503,
            {"detail": "The AI service is experiencing high demand. Please try again in a moment."},
        )
    )
    monkeypatch.setattr(llm_service, "_post", mock_post)

    message = MagicMock()
    message.chat.id = 12345
    message.bot = MagicMock()
    message.bot.send_chat_action = AsyncMock()
    message.answer = AsyncMock()

    state = MagicMock()
    state.get_data = AsyncMock(return_value={})
    state.update_data = AsyncMock()

    await _process_llm_request(
        message=message,
        state=state,
        user_db_id=1,
        text="Hello",
    )

    message.answer.assert_awaited_once()
    called_text = message.answer.await_args.args[0]
    assert "high demand" in called_text
    assert called_text != "Something went wrong"
