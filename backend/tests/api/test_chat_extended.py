import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.crud.crud_user import user as crud_user
from app.crud.crud_chat import chat as crud_chat
from app.crud.crud_session import chat_session as crud_session
from app.schemas.user import UserCreate
from app.schemas.chat import ChatHistoryCreate, ChatSessionCreate

@pytest.mark.asyncio
async def test_read_chat_history_all(client: AsyncClient, db_session: AsyncSession, auth_user: dict) -> None:
    headers = auth_user["headers"]
    user = auth_user["user"]
    session_data = ChatSessionCreate(user_id=user.id, title="s1")
    session = await crud_session.create(db_session, obj_in=session_data)

    chat_data = ChatHistoryCreate(user_id=user.id, session_id=session.id, role="user", content="msg")
    await crud_chat.create(db_session, obj_in=chat_data)

    response = await client.get(f"{settings.API_V1_STR}/chat/", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1

@pytest.mark.asyncio
async def test_create_chat_message_user_not_found(client: AsyncClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    chat_data = {
        "user_id": 999999,
        "role": "user",
        "content": "msg",
        "session_id": 1,
    }
    response = await client.post(f"{settings.API_V1_STR}/chat/", json=chat_data, headers=headers)
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_read_chat_message_by_id(client: AsyncClient, db_session: AsyncSession, auth_user: dict) -> None:
    headers = auth_user["headers"]
    user = auth_user["user"]
    session_data = ChatSessionCreate(user_id=user.id, title="s1")
    session = await crud_session.create(db_session, obj_in=session_data)

    chat_data = ChatHistoryCreate(user_id=user.id, session_id=session.id, role="user", content="msg")
    chat = await crud_chat.create(db_session, obj_in=chat_data)

    response = await client.get(f"{settings.API_V1_STR}/chat/{chat.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == chat.id

@pytest.mark.asyncio
async def test_read_chat_message_not_found(client: AsyncClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    response = await client.get(f"{settings.API_V1_STR}/chat/999999", headers=headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_chat_message(client: AsyncClient, db_session: AsyncSession, auth_user: dict) -> None:
    headers = auth_user["headers"]
    user = auth_user["user"]
    session_data = ChatSessionCreate(user_id=user.id, title="s1")
    session = await crud_session.create(db_session, obj_in=session_data)

    chat_data = ChatHistoryCreate(user_id=user.id, session_id=session.id, role="user", content="msg")
    chat = await crud_chat.create(db_session, obj_in=chat_data)

    response = await client.delete(f"{settings.API_V1_STR}/chat/{chat.id}", headers=headers)
    assert response.status_code == 200

    response = await client.get(f"{settings.API_V1_STR}/chat/{chat.id}", headers=headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_chat_message_not_found(client: AsyncClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    response = await client.delete(f"{settings.API_V1_STR}/chat/999999", headers=headers)
    assert response.status_code == 404
