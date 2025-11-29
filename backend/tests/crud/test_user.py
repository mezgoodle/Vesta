import pytest
from app.crud.crud_user import user as crud_user
from app.schemas.user import UserCreate
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession) -> None:
    telegram_id = 123456789
    user_in = UserCreate(
        telegram_id=telegram_id,
        full_name="Test User",
        username="testuser",
        timezone="UTC",
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    assert user.telegram_id == telegram_id
    assert user.full_name == "Test User"
    assert hasattr(user, "id")


@pytest.mark.asyncio
async def test_get_user_by_telegram_id(db_session: AsyncSession) -> None:
    telegram_id = 987654321
    user_in = UserCreate(
        telegram_id=telegram_id, full_name="Another User", username="anotheruser"
    )
    await crud_user.create(db_session, obj_in=user_in)

    user = await crud_user.get_by_telegram_id(db_session, telegram_id=telegram_id)
    assert user
    assert user.telegram_id == telegram_id
    assert user.username == "anotheruser"
