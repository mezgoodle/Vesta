
import pytest
from unittest.mock import AsyncMock
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
async def test_process_chat_message_session_not_found(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_user: dict,
    mock_llm_service: AsyncMock,
) -> None:
    """Test error handling when session doesn't exist."""
    user = auth_user["user"]
    headers = auth_user["headers"]

    chat_request = {
        "user_id": user.id,
        "message": "Hello",
        "session_id": 99999
    }

    response = await client.post(
        f"{settings.API_V1_STR}/chat/process",
        json=chat_request,
        headers=headers,
    )

    assert response.status_code == 404
    detail = response.json()["detail"]
    assert "Session not found" in detail

@pytest.mark.asyncio
async def test_process_chat_message_session_access_denied(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_user: dict,
    mock_llm_service: AsyncMock,
) -> None:
    """Test error handling when accessing another user's session."""
    user = auth_user["user"]
    headers = auth_user["headers"]

    # Create another user and session
    other_user_in = UserCreate(
        telegram_id=999888777,
        full_name="Other User",
        username="otheruser",
        email="other@example.com",
        password="password"
    )
    other_user = await crud_user.create(db_session, obj_in=other_user_in)

    session_in = ChatSessionCreate(user_id=other_user.id, title="Other Session")
    session = await crud_session.create(db_session, obj_in=session_in)

    chat_request = {
        "user_id": user.id,
        "message": "Hello",
        "session_id": session.id
    }

    response = await client.post(
        f"{settings.API_V1_STR}/chat/process",
        json=chat_request,
        headers=headers,
    )

    assert response.status_code == 403
    detail = response.json()["detail"]
    assert "Session does not belong to user" in detail

@pytest.mark.asyncio
async def test_read_chat_message_by_id(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_user: dict,
) -> None:
    """Test retrieving a specific chat message."""
    user = auth_user["user"]

    # Create a session first to link message to (required by FK)
    session_in = ChatSessionCreate(user_id=user.id, title="Test Session")
    session = await crud_session.create(db_session, obj_in=session_in)

    # Create a message
    message_in = ChatHistoryCreate(
        user_id=user.id,
        session_id=session.id,
        role=ChatRole.USER,
        content="Test Message"
    )
    message = await crud_chat.create(db_session, obj_in=message_in)

    response = await client.get(f"{settings.API_V1_STR}/chat/{message.id}")

    assert response.status_code == 200
    content = response.json()
    assert content["id"] == message.id
    assert content["content"] == "Test Message"

@pytest.mark.asyncio
async def test_read_chat_message_not_found(
    client: AsyncClient,
) -> None:
    """Test retrieving a non-existent chat message."""
    response = await client.get(f"{settings.API_V1_STR}/chat/99999")

    assert response.status_code == 404
    detail = response.json()["detail"]
    assert "Chat message not found" in detail

@pytest.mark.asyncio
async def test_delete_chat_message(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_user: dict,
) -> None:
    """Test deleting a chat message."""
    user = auth_user["user"]

    # Create a session first
    session_in = ChatSessionCreate(user_id=user.id, title="Test Session")
    session = await crud_session.create(db_session, obj_in=session_in)

    # Create a message
    message_in = ChatHistoryCreate(
        user_id=user.id,
        session_id=session.id,
        role=ChatRole.USER,
        content="To Delete"
    )
    message = await crud_chat.create(db_session, obj_in=message_in)

    response = await client.delete(f"{settings.API_V1_STR}/chat/{message.id}")

    assert response.status_code == 200
    content = response.json()
    assert content["id"] == message.id

    # Verify it's gone
    # get() on crud might return None, so let's use client to check
    get_response = await client.get(f"{settings.API_V1_STR}/chat/{message.id}")
    assert get_response.status_code == 404

@pytest.mark.asyncio
async def test_delete_chat_message_not_found(
    client: AsyncClient,
) -> None:
    """Test deleting a non-existent chat message."""
    response = await client.delete(f"{settings.API_V1_STR}/chat/99999")

    assert response.status_code == 404
    detail = response.json()["detail"]
    assert "Chat message not found" in detail

@pytest.mark.asyncio
async def test_read_chat_history_all(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_user: dict,
) -> None:
    """Test retrieving all chat history (no user filter)."""
    user = auth_user["user"]

    # Create session
    session_in = ChatSessionCreate(user_id=user.id, title="Test Session")
    session = await crud_session.create(db_session, obj_in=session_in)

    message_in = ChatHistoryCreate(
        user_id=user.id,
        session_id=session.id,
        role=ChatRole.USER,
        content="Test All"
    )
    await crud_chat.create(db_session, obj_in=message_in)

    response = await client.get(f"{settings.API_V1_STR}/chat/")

    assert response.status_code == 200
    content = response.json()
    assert len(content) >= 1
    # Check that at least one message is from our user
    assert any(msg["content"] == "Test All" for msg in content)

@pytest.mark.asyncio
async def test_read_chat_sessions_all(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_user: dict,
) -> None:
    """Test retrieving all chat sessions (no user filter)."""
    user = auth_user["user"]

    session_in = ChatSessionCreate(
        user_id=user.id,
        title="Test Session All"
    )
    await crud_session.create(db_session, obj_in=session_in)

    response = await client.get(f"{settings.API_V1_STR}/chat/sessions")

    assert response.status_code == 200
    content = response.json()
    assert len(content) >= 1
    assert any(s["title"] == "Test Session All" for s in content)
