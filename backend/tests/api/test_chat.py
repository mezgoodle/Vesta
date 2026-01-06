from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.crud_chat import chat as crud_chat
from app.crud.crud_user import user as crud_user
from app.main import app
from app.schemas.chat import ChatHistoryCreate
from app.schemas.user import UserCreate
from app.services.llm import LLMService


@pytest.mark.asyncio
async def test_create_chat_message(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # Create a user first
    user_in = UserCreate(
        telegram_id=111222333, full_name="Chat User", username="chatuser"
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    # Create chat message
    chat_data = {"user_id": user.id, "role": "user", "content": "Hello, world!"}
    response = await client.post(f"{settings.API_V1_STR}/chat/", json=chat_data)

    assert response.status_code == 200
    content = response.json()
    assert content["role"] == chat_data["role"]
    assert content["content"] == chat_data["content"]
    assert content["user_id"] == user.id
    assert "id" in content


@pytest.mark.asyncio
async def test_process_chat_message_success(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Test successful chat message processing with mocked LLM service."""
    # Create mock LLM service
    mock_llm_service = AsyncMock(spec=LLMService)
    mock_llm_service.chat = AsyncMock(return_value="This is a mocked AI response")
    mock_llm_service.close = AsyncMock()

    # Override the dependency
    from app.services.llm import llm_service as llm_service_dep

    async def mock_llm_service_dep():
        yield mock_llm_service

    app.dependency_overrides[llm_service_dep] = mock_llm_service_dep

    try:
        # Create a user
        user_in = UserCreate(
            telegram_id=777888999, full_name="Process User", username="processuser"
        )
        user = await crud_user.create(db_session, obj_in=user_in)

        # Send chat request
        chat_request = {"user_id": user.telegram_id, "message": "Hello, AI!"}
        response = await client.post(
            f"{settings.API_V1_STR}/chat/process", json=chat_request
        )

        # Verify response
        assert response.status_code == 200
        content = response.json()
        assert content["response"] == "This is a mocked AI response"
        assert "user_message_id" in content
        assert "assistant_message_id" in content

        # Verify messages were saved to database
        user_messages = await crud_chat.get_by_user_id(db_session, user_id=user.id)
        assert len(user_messages) == 2

        # Verify user message
        user_msg = next(msg for msg in user_messages if msg.role == "user")
        assert user_msg.content == "Hello, AI!"
        assert user_msg.user_id == user.id

        # Verify assistant message
        assistant_msg = next(msg for msg in user_messages if msg.role == "assistant")
        assert assistant_msg.content == "This is a mocked AI response"
        assert assistant_msg.user_id == user.id

        # Verify LLM service was called
        mock_llm_service.chat.assert_called_once()
    finally:
        # Clean up dependency override
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_process_chat_message_user_not_found(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test error handling when user doesn't exist."""
    # Create mock LLM service (even if not used, keeps cleanup consistent)
    mock_llm_service = AsyncMock(spec=LLMService)
    mock_llm_service.close = AsyncMock()

    # Override the dependency
    from app.services.llm import llm_service as llm_service_dep

    async def mock_llm_service_dep():
        yield mock_llm_service

    app.dependency_overrides[llm_service_dep] = mock_llm_service_dep

    try:
        chat_request = {"user_id": 99999, "message": "Hello"}
        response = await client.post(
            f"{settings.API_V1_STR}/chat/process", json=chat_request
        )

        assert response.status_code == 404
        content = response.json()
        assert "User not found" in content["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_process_chat_message_llm_error(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Test error handling when LLM service fails."""
    # Create mock LLM service that raises an exception
    mock_llm_service = AsyncMock(spec=LLMService)
    mock_llm_service.chat = AsyncMock(side_effect=Exception("LLM API error"))
    mock_llm_service.close = AsyncMock()

    # Override the dependency
    from app.services.llm import llm_service as llm_service_dep

    async def mock_llm_service_dep():
        yield mock_llm_service

    app.dependency_overrides[llm_service_dep] = mock_llm_service_dep

    try:
        # Create a user
        user_in = UserCreate(
            telegram_id=888999000, full_name="Error User", username="erroruser"
        )
        user = await crud_user.create(db_session, obj_in=user_in)

        # Send chat request
        chat_request = {"user_id": user.telegram_id, "message": "This will fail"}
        response = await client.post(
            f"{settings.API_V1_STR}/chat/process", json=chat_request
        )

        # Verify error response
        assert response.status_code == 500
        content = response.json()
        assert "Failed to process chat message" in content["detail"]

        # Verify user message was still saved
        user_messages = await crud_chat.get_by_user_id(db_session, user_id=user.id)
        assert len(user_messages) == 1
        assert user_messages[0].role == "user"
        assert user_messages[0].content == "This will fail"
    finally:
        # Clean up dependency override
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_process_chat_message_with_history(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Test that conversation history is properly passed to LLM service."""
    # Create mock LLM service
    mock_llm_service = AsyncMock(spec=LLMService)
    mock_llm_service.chat = AsyncMock(return_value="Response with context")
    mock_llm_service.close = AsyncMock()

    # Override the dependency
    from app.services.llm import llm_service as llm_service_dep

    async def mock_llm_service_dep():
        yield mock_llm_service

    app.dependency_overrides[llm_service_dep] = mock_llm_service_dep

    try:
        # Create a user
        user_in = UserCreate(
            telegram_id=999000111, full_name="History User", username="historyuser"
        )
        user = await crud_user.create(db_session, obj_in=user_in)

        # Create existing conversation history
        history_messages = [
            ("user", "First question"),
            ("assistant", "First answer"),
            ("user", "Second question"),
            ("assistant", "Second answer"),
        ]

        for role, content in history_messages:
            chat_in = ChatHistoryCreate(user_id=user.id, role=role, content=content)
            await crud_chat.create(db_session, obj_in=chat_in)

        # Send new message
        chat_request = {"user_id": user.telegram_id, "message": "Third question"}
        response = await client.post(
            f"{settings.API_V1_STR}/chat/process", json=chat_request
        )

        assert response.status_code == 200

        # Verify LLM service was called with history
        mock_llm_service.chat.assert_called_once()
        call_args = mock_llm_service.chat.call_args

        # Verify the user text
        assert call_args.kwargs["user_text"] == "Third question"

        # Verify history was passed
        history_records = call_args.kwargs["history_records"]
        assert len(history_records) == 4

        # Verify history is in correct order (oldest to newest)
        assert history_records[0].content == "First question"
        assert history_records[0].role == "user"
        assert history_records[1].content == "First answer"
        assert history_records[1].role == "assistant"
        assert history_records[-1].content == "Second answer"
        assert history_records[-1].role == "assistant"

        # Verify total messages in database (4 old + 1 user + 1 assistant = 6)
        all_messages = await crud_chat.get_by_user_id(db_session, user_id=user.id)
        assert len(all_messages) == 6
    finally:
        # Clean up dependency override
        app.dependency_overrides.clear()
