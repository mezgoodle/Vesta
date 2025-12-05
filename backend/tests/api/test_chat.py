import pytest
from app.core.config import settings
from app.crud.crud_user import user as crud_user
from app.schemas.user import UserCreate
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


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
