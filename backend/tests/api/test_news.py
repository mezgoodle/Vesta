import pytest
from app.core.config import settings
from app.crud.crud_user import user as crud_user
from app.crud.crud_news import news as crud_news
from app.schemas.user import UserCreate
from app.schemas.news import NewsSubscriptionCreate
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture
async def test_user(db_session: AsyncSession):
    user_in = UserCreate(telegram_id=505050505, full_name="News API User", username="newsapi")
    return await crud_user.create(db_session, obj_in=user_in)

@pytest.fixture
async def test_news_subscription(db_session: AsyncSession, test_user):
    news_in = NewsSubscriptionCreate(topic="Test News", schedule_time="08:00:00", is_active=True, user_id=test_user.id)
    return await crud_news.create(db_session, obj_in=news_in)

@pytest.mark.asyncio
async def test_create_news_subscription_api(client: AsyncClient, test_user) -> None:
    news_data = {
        "topic": "API News",
        "schedule_time": "08:00:00",
        "is_active": True,
        "user_id": test_user.id,
    }
    response = await client.post(f"{settings.API_V1_STR}/news/", json=news_data)
    assert response.status_code == 200
    content = response.json()
    assert content["topic"] == news_data["topic"]
    assert content["user_id"] == test_user.id

@pytest.mark.asyncio
async def test_create_news_subscription_user_not_found(client: AsyncClient) -> None:
    news_data = {
        "topic": "API News",
        "schedule_time": "08:00:00",
        "is_active": True,
        "user_id": 999,
    }
    response = await client.post(f"{settings.API_V1_STR}/news/", json=news_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

@pytest.mark.asyncio
async def test_read_news_subscriptions_api(client: AsyncClient, test_news_subscription) -> None:
    response = await client.get(f"{settings.API_V1_STR}/news/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

@pytest.mark.asyncio
async def test_read_news_subscriptions_by_user(client: AsyncClient, test_user, test_news_subscription) -> None:
    response = await client.get(f"{settings.API_V1_STR}/news/?user_id={test_user.id}")
    assert response.status_code == 200
    content = response.json()
    assert isinstance(content, list)
    assert len(content) > 0
    assert content[0]["user_id"] == test_user.id

@pytest.mark.asyncio
async def test_read_news_subscription_api(client: AsyncClient, test_news_subscription) -> None:
    response = await client.get(f"{settings.API_V1_STR}/news/{test_news_subscription.id}")
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == test_news_subscription.id

@pytest.mark.asyncio
async def test_read_news_subscription_not_found(client: AsyncClient) -> None:
    response = await client.get(f"{settings.API_V1_STR}/news/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "News subscription not found"

@pytest.mark.asyncio
async def test_update_news_subscription_api(client: AsyncClient, test_news_subscription) -> None:
    update_data = {"topic": "Updated News"}
    response = await client.put(f"{settings.API_V1_STR}/news/{test_news_subscription.id}", json=update_data)
    assert response.status_code == 200
    content = response.json()
    assert content["topic"] == "Updated News"

@pytest.mark.asyncio
async def test_update_news_subscription_not_found(client: AsyncClient) -> None:
    update_data = {"topic": "Updated News"}
    response = await client.put(f"{settings.API_V1_STR}/news/999", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "News subscription not found"

@pytest.mark.asyncio
async def test_delete_news_subscription_api(client: AsyncClient, test_news_subscription) -> None:
    response = await client.delete(f"{settings.API_V1_STR}/news/{test_news_subscription.id}")
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == test_news_subscription.id

    response = await client.get(f"{settings.API_V1_STR}/news/{test_news_subscription.id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_news_subscription_not_found(client: AsyncClient) -> None:
    response = await client.delete(f"{settings.API_V1_STR}/news/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "News subscription not found"
