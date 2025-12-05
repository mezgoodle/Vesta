import pytest
from app.core.config import settings
from app.crud.crud_user import user as crud_user
from app.schemas.user import UserCreate
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_user_api(client: AsyncClient, db_session: AsyncSession) -> None:
    user_data = {
        "telegram_id": 101010101,
        "full_name": "API User",
        "username": "apiuser",
        "timezone": "UTC",
    }
    response = await client.post(f"{settings.API_V1_STR}/users/", json=user_data)
    assert response.status_code == 200
    content = response.json()
    assert content["telegram_id"] == user_data["telegram_id"]
    assert content["username"] == user_data["username"]
    assert "id" in content


@pytest.mark.asyncio
async def test_read_users_api(client: AsyncClient, db_session: AsyncSession) -> None:
    user_in = UserCreate(
        telegram_id=202020202, full_name="Read User", username="readuser"
    )
    await crud_user.create(db_session, obj_in=user_in)

    response = await client.get(f"{settings.API_V1_STR}/users/")
    assert response.status_code == 200
    content = response.json()
    assert len(content) >= 1


@pytest.mark.asyncio
async def test_read_user_by_id_api(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user_in = UserCreate(telegram_id=303030303, full_name="ID User", username="iduser")
    user = await crud_user.create(db_session, obj_in=user_in)

    response = await client.get(f"{settings.API_V1_STR}/users/{user.id}")
    assert response.status_code == 200
    content = response.json()
    assert content["telegram_id"] == user_in.telegram_id
