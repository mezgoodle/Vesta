from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.crud_chat import chat as crud_chat
from app.crud.crud_session import chat_session as crud_session
from app.crud.crud_user import user as crud_user
from app.schemas.chat import ChatHistoryCreate, ChatSessionCreate
from app.schemas.enums import ChatRole
from app.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_read_chat_history(client: AsyncClient, db_session: AsyncSession) -> None:
    # Create a user first
    user_in = UserCreate(
        telegram_id=111222333, full_name="Chat User", username="chatuser"
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    # Create chat session
    chat_session_in = ChatSessionCreate(user_id=user.id, title="Chat Session")
    chat_session = await crud_session.create(db_session, obj_in=chat_session_in)

    # Create chat history
    chat_history_in = ChatHistoryCreate(
        user_id=user.id,
        session_id=chat_session.id,
        role="user",
        content="Hello, world!",
    )
    chat_history = await crud_chat.create(db_session, obj_in=chat_history_in)
    _ = await crud_chat.create(db_session, obj_in=chat_history_in)

    response = await client.get(f"{settings.API_V1_STR}/chat/?user_id={user.id}")

    assert response.status_code == 200
    content = response.json()
    assert len(content) == 2
    assert content[0]["role"] == chat_history.role
    assert content[0]["content"] == chat_history.content
    assert content[0]["user_id"] == user.id
    assert "id" in content[0]


@pytest.mark.asyncio
async def test_read_chat_sessions(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # Create a user first
    user_in = UserCreate(
        telegram_id=111222333, full_name="Chat User", username="chatuser"
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    # Create chat session
    chat_session_in = ChatSessionCreate(user_id=user.id, title="Chat Session")
    chat_session = await crud_session.create(db_session, obj_in=chat_session_in)

    response = await client.get(f"{settings.API_V1_STR}/sessions/?user_id={user.id}")

    assert response.status_code == 200
    content = response.json()
    assert len(content) == 1
    assert content[0]["title"] == chat_session.title
    assert content[0]["user_id"] == user.id
    assert "id" in content[0]


@pytest.mark.asyncio
async def test_create_chat_message_user_not_found(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # Create chat message for non-existent user
    chat_data = {
        "user_id": 99999,
        "role": "user",
        "content": "Hello, world!",
        "session_id": 1,
    }
    response = await client.post(f"{settings.API_V1_STR}/chat/", json=chat_data)

    assert response.status_code == 404
    content = response.json()
    assert "User not found" in content["detail"]


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
    chat_data = {
        "user_id": user.id,
        "role": "user",
        "content": "Hello, world!",
        "session_id": 1,
    }
    response = await client.post(f"{settings.API_V1_STR}/chat/", json=chat_data)

    assert response.status_code == 200
    content = response.json()
    assert content["role"] == chat_data["role"]
    assert content["content"] == chat_data["content"]
    assert content["user_id"] == user.id
    assert "id" in content


@pytest.mark.asyncio
async def test_read_chat_message_success(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # Create a user
    user_in = UserCreate(
        telegram_id=111222333, full_name="Chat User", username="chatuser"
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    # Create chat session
    chat_session_in = ChatSessionCreate(user_id=user.id, title="Chat Session")
    chat_session = await crud_session.create(db_session, obj_in=chat_session_in)

    # Create chat message
    chat_history_in = ChatHistoryCreate(
        user_id=user.id,
        session_id=chat_session.id,
        role="user",
        content="Read me!",
    )
    chat_history = await crud_chat.create(db_session, obj_in=chat_history_in)

    response = await client.get(f"{settings.API_V1_STR}/chat/{chat_history.id}")

    assert response.status_code == 200
    content = response.json()
    assert content["role"] == "user"
    assert content["content"] == "Read me!"
    assert content["user_id"] == user.id
    assert content["id"] == chat_history.id


@pytest.mark.asyncio
async def test_read_chat_message_not_found(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    response = await client.get(f"{settings.API_V1_STR}/chat/99999")

    assert response.status_code == 404
    content = response.json()
    assert "Chat message not found" in content["detail"]


@pytest.mark.asyncio
async def test_delete_chat_message_success(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # Create a user
    user_in = UserCreate(
        telegram_id=111222333, full_name="Chat User", username="chatuser"
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    # Create chat session
    chat_session_in = ChatSessionCreate(user_id=user.id, title="Chat Session")
    chat_session = await crud_session.create(db_session, obj_in=chat_session_in)

    # Create chat message
    chat_history_in = ChatHistoryCreate(
        user_id=user.id,
        session_id=chat_session.id,
        role="user",
        content="Delete me!",
    )
    chat_history = await crud_chat.create(db_session, obj_in=chat_history_in)

    response = await client.delete(f"{settings.API_V1_STR}/chat/{chat_history.id}")

    assert response.status_code == 200
    content = response.json()
    assert content["role"] == "user"
    assert content["content"] == "Delete me!"
    assert content["id"] == chat_history.id

    # Verify it was deleted
    deleted_chat = await crud_chat.get(db_session, id=chat_history.id)
    assert deleted_chat is None


@pytest.mark.asyncio
async def test_delete_chat_message_not_found(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    response = await client.delete(f"{settings.API_V1_STR}/chat/99999")

    assert response.status_code == 404
    content = response.json()
    assert "Chat message not found" in content["detail"]


@pytest.mark.asyncio
async def test_process_chat_message_success(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_llm_service: AsyncMock,
    auth_user: dict,
) -> None:
    """Test successful chat message processing with mocked LLM service."""
    # Setup mock
    mock_llm_service.chat.return_value = "This is a mocked AI response"

    # Use authenticated user
    user = auth_user["user"]
    headers = auth_user["headers"]

    # Send chat request with authentication
    chat_request = {"user_id": user.id, "message": "Hello, AI!"}
    response = await client.post(
        f"{settings.API_V1_STR}/chat/process",
        json=chat_request,
        headers=headers,
    )

    # Verify response
    assert response.status_code == 200
    content = response.json()
    assert content["response"] == "This is a mocked AI response"
    assert "user_message_id" in content
    assert "assistant_message_id" in content
    assert "session_id" in content

    # Verify messages were saved to database
    user_messages = await crud_chat.get_by_user_id(db_session, user_id=user.id)
    assert len(user_messages) == 2

    # Verify user message
    user_msg = next(msg for msg in user_messages if msg.role == "user")
    assert user_msg.content == "Hello, AI!"
    assert user_msg.user_id == user.id
    assert user_msg.session_id == content["session_id"]

    # Verify assistant message
    assistant_msg = next(msg for msg in user_messages if msg.role == "model")
    assert assistant_msg.content == "This is a mocked AI response"
    assert assistant_msg.user_id == user.id
    assert assistant_msg.session_id == content["session_id"]

    # Verify LLM service was called
    mock_llm_service.chat.assert_called_once()


@pytest.mark.asyncio
async def test_process_chat_message_user_not_found(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_llm_service: AsyncMock,
    auth_user: dict,
) -> None:
    """Test error handling when user doesn't exist."""
    headers = auth_user["headers"]
    chat_request = {"user_id": 99999, "message": "Hello"}
    response = await client.post(
        f"{settings.API_V1_STR}/chat/process",
        json=chat_request,
        headers=headers,
    )

    assert response.status_code == 404
    content = response.json()
    assert "User not found" in content["detail"]


@pytest.mark.asyncio
async def test_process_chat_message_session_not_found(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_llm_service: AsyncMock,
    auth_user: dict,
) -> None:
    """Test error handling when session doesn't exist."""
    headers = auth_user["headers"]
    user = auth_user["user"]
    chat_request = {"user_id": user.id, "message": "Hello", "session_id": 99999}
    response = await client.post(
        f"{settings.API_V1_STR}/chat/process",
        json=chat_request,
        headers=headers,
    )

    assert response.status_code == 404
    content = response.json()
    assert "Session not found" in content["detail"]


@pytest.mark.asyncio
async def test_process_chat_message_session_wrong_user(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_llm_service: AsyncMock,
    auth_user: dict,
) -> None:
    """Test error handling when session belongs to a different user."""
    headers = auth_user["headers"]
    user = auth_user["user"]

    # Create another user
    other_user_in = UserCreate(
        telegram_id=999888777, full_name="Other User", username="otheruser"
    )
    other_user = await crud_user.create(db_session, obj_in=other_user_in)

    # Create a session belonging to the other user
    session_in = ChatSessionCreate(user_id=other_user.id, title="Other Session")
    session = await crud_session.create(db_session, obj_in=session_in)

    chat_request = {
        "user_id": user.id,
        "message": "Hello",
        "session_id": session.id,
    }
    response = await client.post(
        f"{settings.API_V1_STR}/chat/process",
        json=chat_request,
        headers=headers,
    )

    assert response.status_code == 403
    content = response.json()
    assert "Session does not belong to user" in content["detail"]


@pytest.mark.asyncio
async def test_process_chat_message_llm_error(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_llm_service: AsyncMock,
    auth_user: dict,
) -> None:
    """Test error handling when LLM service fails."""
    # Setup mock to raise an exception
    mock_llm_service.chat.side_effect = Exception("LLM API error")

    # Use authenticated user
    user = auth_user["user"]
    headers = auth_user["headers"]

    # Send chat request with authentication
    chat_request = {"user_id": user.id, "message": "This will fail"}
    response = await client.post(
        f"{settings.API_V1_STR}/chat/process",
        json=chat_request,
        headers=headers,
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


@pytest.mark.asyncio
async def test_process_chat_message_with_history(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_llm_service: AsyncMock,
    auth_user: dict,
) -> None:
    """Test that conversation history is properly passed to LLM service."""
    # Setup mock
    mock_llm_service.chat.return_value = "Response with context"

    # Use authenticated user
    user = auth_user["user"]
    headers = auth_user["headers"]

    # Create a session
    session_in = ChatSessionCreate(user_id=user.id, title="History Session")
    session = await crud_session.create(db_session, obj_in=session_in)

    # Create existing conversation history
    history_messages = [
        (ChatRole.USER, "First question"),
        (ChatRole.MODEL, "First answer"),
        (ChatRole.USER, "Second question"),
        (ChatRole.MODEL, "Second answer"),
    ]

    for role, content in history_messages:
        chat_in = ChatHistoryCreate(
            user_id=user.id,
            role=role,
            content=content,
            session_id=session.id,
        )
        await crud_chat.create(db_session, obj_in=chat_in)

    # Send new message with authentication
    chat_request = {
        "user_id": user.id,
        "message": "Third question",
        "session_id": session.id,
    }
    response = await client.post(
        f"{settings.API_V1_STR}/chat/process",
        json=chat_request,
        headers=headers,
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
    assert history_records[0].role == ChatRole.USER
    assert history_records[1].content == "First answer"
    assert history_records[1].role == ChatRole.MODEL
    assert history_records[-1].content == "Second answer"
    assert history_records[-1].role == ChatRole.MODEL

    # Verify total messages in database (4 old + 1 user + 1 assistant = 6)
    all_messages = await crud_chat.get_by_user_id(db_session, user_id=user.id)
    assert len(all_messages) == 6


@pytest.mark.asyncio
async def test_process_chat_message_background_task(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_llm_service: AsyncMock,
    auth_user: dict,
) -> None:
    """Test that background task is added when total messages reach SUMMARY_MESSAGE_WINDOW."""
    # Setup mock
    mock_llm_service.chat.return_value = "Response with context"

    # Use authenticated user
    user = auth_user["user"]
    headers = auth_user["headers"]

    # Create a session
    session_in = ChatSessionCreate(user_id=user.id, title="History Session")
    session = await crud_session.create(db_session, obj_in=session_in)

    # We need SUMMARY_MESSAGE_WINDOW messages in total to trigger the task.
    # SUMMARY_MESSAGE_WINDOW is 6. The process endpoint creates 2 messages
    # (1 user, 1 assistant). So we pre-populate 4 messages.
    history_messages = [
        (ChatRole.USER, "1"),
        (ChatRole.MODEL, "2"),
        (ChatRole.USER, "3"),
        (ChatRole.MODEL, "4"),
    ]

    for role, content in history_messages:
        chat_in = ChatHistoryCreate(
            user_id=user.id,
            role=role,
            content=content,
            session_id=session.id,
        )
        await crud_chat.create(db_session, obj_in=chat_in)

    # Send new message with authentication
    chat_request = {
        "user_id": user.id,
        "message": "5",
        "session_id": session.id,
    }

    # We patch BackgroundTasks.add_task to verify it's called
    from unittest.mock import patch
    with patch("fastapi.BackgroundTasks.add_task") as mock_add_task:
        response = await client.post(
            f"{settings.API_V1_STR}/chat/process",
            json=chat_request,
            headers=headers,
        )

        assert response.status_code == 200
        # Check that add_task was called (since 4 + 2 = 6, which is % 6 == 0)
        mock_add_task.assert_called_once()


@pytest.mark.asyncio
async def test_process_chat_message_with_session(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_llm_service: AsyncMock,
    auth_user: dict,
) -> None:
    """Test that session is properly passed to LLM service."""
    # Setup mock
    mock_llm_service.chat.return_value = "Response with context"

    # Use authenticated user
    user = auth_user["user"]
    headers = auth_user["headers"]

    # Create a session
    session_in = ChatSessionCreate(user_id=user.id, title="History Session")
    session = await crud_session.create(db_session, obj_in=session_in)

    # Send new message with authentication
    chat_request = {
        "user_id": user.id,
        "message": "Hello",
        "session_id": session.id,
    }
    response = await client.post(
        f"{settings.API_V1_STR}/chat/process",
        json=chat_request,
        headers=headers,
    )

    assert response.status_code == 200

    content = response.json()
    assert content["response"] == "Response with context"
    assert content["user_message_id"] == 1
    assert content["assistant_message_id"] == 2
    assert content["session_id"] == session.id

@pytest.mark.asyncio
async def test_read_chat_history_with_user_id(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_user: dict,
) -> None:
    headers = auth_user["headers"]
    user = auth_user["user"]

    response = await client.get(
        f"{settings.API_V1_STR}/chat/?user_id={user.id}",
        headers=headers,
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_read_chat_history_all(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_user: dict,
) -> None:
    headers = auth_user["headers"]

    response = await client.get(
        f"{settings.API_V1_STR}/chat/",
        headers=headers,
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_create_chat_message(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_user: dict,
) -> None:
    headers = auth_user["headers"]
    user = auth_user["user"]

    data = {
        "user_id": user.id,
        "session_id": 1,
        "role": "user",
        "content": "Test message"
    }
    response = await client.post(
        f"{settings.API_V1_STR}/chat/",
        json=data,
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["content"] == "Test message"

@pytest.mark.asyncio
async def test_create_chat_message_user_not_found(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_user: dict,
) -> None:
    headers = auth_user["headers"]

    data = {
        "user_id": 9999,
        "session_id": 1,
        "role": "user",
        "content": "Test message"
    }
    response = await client.post(
        f"{settings.API_V1_STR}/chat/",
        json=data,
        headers=headers,
    )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_read_chat_message(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_user: dict,
) -> None:
    headers = auth_user["headers"]
    user = auth_user["user"]

    # create message
    data = {
        "user_id": user.id,
        "session_id": 1,
        "role": "user",
        "content": "Test message"
    }
    response = await client.post(
        f"{settings.API_V1_STR}/chat/",
        json=data,
        headers=headers,
    )
    chat_id = response.json()["id"]

    response = await client.get(
        f"{settings.API_V1_STR}/chat/{chat_id}",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == chat_id

@pytest.mark.asyncio
async def test_read_chat_message_not_found(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_user: dict,
) -> None:
    headers = auth_user["headers"]

    response = await client.get(
        f"{settings.API_V1_STR}/chat/9999",
        headers=headers,
    )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_chat_message(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_user: dict,
) -> None:
    headers = auth_user["headers"]
    user = auth_user["user"]

    # create message
    data = {
        "user_id": user.id,
        "session_id": 1,
        "role": "user",
        "content": "Test message"
    }
    response = await client.post(
        f"{settings.API_V1_STR}/chat/",
        json=data,
        headers=headers,
    )
    chat_id = response.json()["id"]

    response = await client.delete(
        f"{settings.API_V1_STR}/chat/{chat_id}",
        headers=headers,
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_delete_chat_message_not_found(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_user: dict,
) -> None:
    headers = auth_user["headers"]

    response = await client.delete(
        f"{settings.API_V1_STR}/chat/9999",
        headers=headers,
    )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_process_chat_message_tts_failure(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_llm_service: AsyncMock,
    auth_user: dict,
) -> None:
    """Test error handling when TTS service fails."""
    mock_llm_service.chat.return_value = "AI response"

    mock_tts = AsyncMock()
    mock_tts.synthesize.side_effect = Exception("TTS API error")

    from app.main import app
    from app.services.google_tts import google_tts_service
    app.dependency_overrides[google_tts_service] = lambda: mock_tts

    try:
        user = auth_user["user"]
        headers = auth_user["headers"]

        chat_request = {"user_id": user.id, "message": "Hello", "want_voice": True}
        response = await client.post(
            f"{settings.API_V1_STR}/chat/process",
            json=chat_request,
            headers=headers,
        )

        assert response.status_code == 200
        content = response.json()
        assert content["response"] == "AI response"
        assert "voice_bytes" not in content or content["voice_bytes"] is None
    finally:
        app.dependency_overrides.pop(google_tts_service, None)

@pytest.mark.asyncio
async def test_process_chat_message_new_session(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_llm_service: AsyncMock,
    auth_user: dict,
) -> None:
    """Test that a new session is created if session_id is None."""
    mock_llm_service.chat.return_value = "Response"

    user = auth_user["user"]
    headers = auth_user["headers"]

    chat_request = {
        "user_id": user.id,
        "message": "Hello new session",
    }
    response = await client.post(
        f"{settings.API_V1_STR}/chat/process",
        json=chat_request,
        headers=headers,
    )

    assert response.status_code == 200
    content = response.json()
    assert content["session_id"] is not None
