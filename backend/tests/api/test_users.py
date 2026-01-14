import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.crud_user import user as crud_user
from app.schemas.user import UserCreate


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
async def test_read_user_by_telegram_id_api(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user_in = UserCreate(
        telegram_id=202020202, full_name="Read User", username="readuser"
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    response = await client.get(
        f"{settings.API_V1_STR}/users/telegram/{user.telegram_id}"
    )
    assert response.status_code == 200
    content = response.json()
    assert content["telegram_id"] == user_in.telegram_id


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


@pytest.mark.asyncio
async def test_approve_user_api(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test approving a user via the approval endpoint."""
    user_in = UserCreate(
        telegram_id=404040404, full_name="Approval User", username="approvaluser"
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    assert user.is_allowed is False

    approval_data = {"is_allowed": True}
    response = await client.patch(
        f"{settings.API_V1_STR}/users/telegram/{user.telegram_id}/approval",
        json=approval_data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["telegram_id"] == user.telegram_id
    assert content["is_allowed"] is True


@pytest.mark.asyncio
async def test_reject_user_api(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test rejecting/blocking a user via the approval endpoint."""
    user_in = UserCreate(
        telegram_id=505050505, full_name="Reject User", username="rejectuser"
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    approval_data = {"is_allowed": False}
    response = await client.patch(
        f"{settings.API_V1_STR}/users/telegram/{user.telegram_id}/approval",
        json=approval_data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["telegram_id"] == user.telegram_id
    assert content["is_allowed"] is False


@pytest.mark.asyncio
async def test_approve_nonexistent_user_api(client: AsyncClient) -> None:
    """Test that approving a non-existent user returns 404."""
    nonexistent_telegram_id = 999999999
    approval_data = {"is_allowed": True}
    response = await client.patch(
        f"{settings.API_V1_STR}/users/telegram/{nonexistent_telegram_id}/approval",
        json=approval_data,
    )
    assert response.status_code == 404
    content = response.json()
    assert "not found" in content["detail"].lower()


@pytest.mark.asyncio
async def test_create_user_defaults_to_not_allowed(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that newly created users have is_allowed=False by default."""
    user_data = {
        "telegram_id": 606060606,
        "full_name": "Default User",
        "username": "defaultuser",
        "timezone": "UTC",
    }
    response = await client.post(f"{settings.API_V1_STR}/users/", json=user_data)
    assert response.status_code == 200
    content = response.json()
    assert content["is_allowed"] is False


@pytest.mark.asyncio
async def test_get_allowed_telegram_ids(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test getting telegram_ids of all allowed users."""
    allowed_user_1 = UserCreate(
        telegram_id=707070707, full_name="Allowed User 1", username="allowed1"
    )
    allowed_user_2 = UserCreate(
        telegram_id=808080808, full_name="Allowed User 2", username="allowed2"
    )
    not_allowed_user = UserCreate(
        telegram_id=909090909, full_name="Not Allowed User", username="notallowed"
    )

    user1 = await crud_user.create(db_session, obj_in=allowed_user_1)
    user2 = await crud_user.create(db_session, obj_in=allowed_user_2)
    await crud_user.create(db_session, obj_in=not_allowed_user)
    await client.patch(
        f"{settings.API_V1_STR}/users/telegram/{user1.telegram_id}/approval",
        json={"is_allowed": True},
    )
    await client.patch(
        f"{settings.API_V1_STR}/users/telegram/{user2.telegram_id}/approval",
        json={"is_allowed": True},
    )

    response = await client.get(f"{settings.API_V1_STR}/users/allowed/telegram-ids")
    assert response.status_code == 200
    telegram_ids = response.json()
    assert isinstance(telegram_ids, list)

    assert len(telegram_ids) == 2
    assert all(isinstance(item, dict) for item in telegram_ids)

    all_telegram_ids = {item["telegram_id"] for item in telegram_ids}
    assert 707070707 in all_telegram_ids
    assert 808080808 in all_telegram_ids
    assert 909090909 not in all_telegram_ids
