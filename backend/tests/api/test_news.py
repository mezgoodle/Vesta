import pytest
from app.core.config import settings
from app.crud.crud_user import user as crud_user
from app.schemas.user import UserCreate
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_news_subscription_api(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user_in = UserCreate(
        telegram_id=505050505, full_name="News API User", username="newsapi"
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    news_data = {
        "topic": "API News",
        "schedule_time": "08:00:00",
        "is_active": True,
        "user_id": user.id,
    }
    response = await client.post(f"{settings.API_V1_STR}/news/", json=news_data)
    assert response.status_code == 200
    content = response.json()
    assert content["topic"] == news_data["topic"]
    assert content["user_id"] == user.id


@pytest.mark.asyncio
async def test_read_news_subscriptions_api(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    response = await client.get(f"{settings.API_V1_STR}/news/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
