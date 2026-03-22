import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.crud.crud_user import user as crud_user
from app.crud.crud_news import news as crud_news
from app.schemas.user import UserCreate
from app.schemas.news import NewsSubscriptionCreate

@pytest.mark.asyncio
async def test_create_news_user_not_found(client: AsyncClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    news_data = {
        "topic": "API News",
        "schedule_time": "08:00:00",
        "is_active": True,
        "user_id": 999999,
    }
    response = await client.post(f"{settings.API_V1_STR}/news/", json=news_data, headers=headers)
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_read_news_by_user_id(client: AsyncClient, db_session: AsyncSession, auth_user: dict) -> None:
    headers = auth_user["headers"]
    user = auth_user["user"]

    news_data = NewsSubscriptionCreate(topic="t1", schedule_time="10:00:00", user_id=user.id)
    await crud_news.create(db_session, obj_in=news_data)

    response = await client.get(f"{settings.API_V1_STR}/news/?user_id={user.id}", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1

@pytest.mark.asyncio
async def test_read_news_by_id(client: AsyncClient, db_session: AsyncSession, auth_user: dict) -> None:
    headers = auth_user["headers"]
    user = auth_user["user"]
    news_data = NewsSubscriptionCreate(topic="t1", schedule_time="10:00:00", user_id=user.id)
    news = await crud_news.create(db_session, obj_in=news_data)

    response = await client.get(f"{settings.API_V1_STR}/news/{news.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == news.id

@pytest.mark.asyncio
async def test_read_news_not_found(client: AsyncClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    response = await client.get(f"{settings.API_V1_STR}/news/999999", headers=headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_news(client: AsyncClient, db_session: AsyncSession, auth_user: dict) -> None:
    headers = auth_user["headers"]
    user = auth_user["user"]
    news_data = NewsSubscriptionCreate(topic="t1", schedule_time="10:00:00", user_id=user.id)
    news = await crud_news.create(db_session, obj_in=news_data)

    update_data = {"topic": "updated"}
    response = await client.put(f"{settings.API_V1_STR}/news/{news.id}", json=update_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["topic"] == "updated"

@pytest.mark.asyncio
async def test_update_news_not_found(client: AsyncClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    response = await client.put(f"{settings.API_V1_STR}/news/999999", json={"topic": "updated"}, headers=headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_news(client: AsyncClient, db_session: AsyncSession, auth_user: dict) -> None:
    headers = auth_user["headers"]
    user = auth_user["user"]
    news_data = NewsSubscriptionCreate(topic="t1", schedule_time="10:00:00", user_id=user.id)
    news = await crud_news.create(db_session, obj_in=news_data)

    response = await client.delete(f"{settings.API_V1_STR}/news/{news.id}", headers=headers)
    assert response.status_code == 200

    # Verify deleted
    response = await client.get(f"{settings.API_V1_STR}/news/{news.id}", headers=headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_news_not_found(client: AsyncClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    response = await client.delete(f"{settings.API_V1_STR}/news/999999", headers=headers)
    assert response.status_code == 404
