import pytest
from app.core.config import settings
from app.crud.crud_user import user as crud_user
from app.crud.crud_news import news as crud_news
from app.schemas.user import UserCreate
from app.schemas.news import NewsSubscriptionCreate
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

@pytest.mark.asyncio
async def test_create_news_subscription_api(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user_in = UserCreate(
        telegram_id=505050505, full_name="News API User", username="newsapi"
    )
    user = await crud_user.create(db_session, obj_in=user_in)
    await db_session.commit()

    news_data = {
        "topic": "API News",
        "schedule_time": "08:00:00",
        "is_active": True,
        "user_id": user.id,
    }
    response = await client.post(f"{settings.API_V1_STR}/news/", json=news_data)
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["topic"] == news_data["topic"]
    assert content["user_id"] == user.id

@pytest.mark.asyncio
async def test_create_news_subscription_api_user_not_found(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    news_data = {
        "topic": "API News Not Found",
        "schedule_time": "08:00:00",
        "is_active": True,
        "user_id": 999999,
    }
    response = await client.post(f"{settings.API_V1_STR}/news/", json=news_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"

@pytest.mark.asyncio
async def test_read_news_subscriptions_api(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    response = await client.get(f"{settings.API_V1_STR}/news/")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_read_news_subscriptions_by_user_id_api(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user_in = UserCreate(
        telegram_id=505050506, full_name="News Read API User", username="newsapiread"
    )
    user = await crud_user.create(db_session, obj_in=user_in)
    await db_session.commit()

    news_data1 = NewsSubscriptionCreate(
        topic="Topic 1", schedule_time="10:00:00", is_active=True, user_id=user.id
    )
    news_data2 = NewsSubscriptionCreate(
        topic="Topic 2", schedule_time="11:00:00", is_active=True, user_id=user.id
    )
    await crud_news.create(db_session, obj_in=news_data1)
    await crud_news.create(db_session, obj_in=news_data2)
    await db_session.commit()

    response = await client.get(f"{settings.API_V1_STR}/news/?user_id={user.id}")
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert len(content) == 2
    assert content[0]["user_id"] == user.id
    assert content[1]["user_id"] == user.id

@pytest.mark.asyncio
async def test_read_news_subscription_api(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user_in = UserCreate(
        telegram_id=505050507, full_name="News Get API User", username="newsapiget"
    )
    user = await crud_user.create(db_session, obj_in=user_in)
    await db_session.commit()

    news_data = NewsSubscriptionCreate(
        topic="Get Topic", schedule_time="09:00:00", is_active=True, user_id=user.id
    )
    news = await crud_news.create(db_session, obj_in=news_data)
    await db_session.commit()

    response = await client.get(f"{settings.API_V1_STR}/news/{news.id}")
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["topic"] == "Get Topic"
    assert content["id"] == news.id

@pytest.mark.asyncio
async def test_read_news_subscription_api_not_found(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    response = await client.get(f"{settings.API_V1_STR}/news/999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "News subscription not found"

@pytest.mark.asyncio
async def test_update_news_subscription_api(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user_in = UserCreate(
        telegram_id=505050508, full_name="News Put API User", username="newsapiput"
    )
    user = await crud_user.create(db_session, obj_in=user_in)
    await db_session.commit()

    news_data = NewsSubscriptionCreate(
        topic="Put Topic", schedule_time="09:00:00", is_active=True, user_id=user.id
    )
    news = await crud_news.create(db_session, obj_in=news_data)
    await db_session.commit()

    update_data = {
        "topic": "Updated Topic",
        "schedule_time": "12:00:00"
    }
    response = await client.put(f"{settings.API_V1_STR}/news/{news.id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["topic"] == "Updated Topic"
    assert content["schedule_time"] == "12:00:00"

@pytest.mark.asyncio
async def test_update_news_subscription_api_not_found(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    update_data = {
        "topic": "Updated Topic"
    }
    response = await client.put(f"{settings.API_V1_STR}/news/999999", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "News subscription not found"

@pytest.mark.asyncio
async def test_delete_news_subscription_api(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user_in = UserCreate(
        telegram_id=505050509, full_name="News Delete API User", username="newsapidel"
    )
    user = await crud_user.create(db_session, obj_in=user_in)
    await db_session.commit()

    news_data = NewsSubscriptionCreate(
        topic="Delete Topic", schedule_time="09:00:00", is_active=True, user_id=user.id
    )
    news = await crud_news.create(db_session, obj_in=news_data)
    await db_session.commit()

    response = await client.delete(f"{settings.API_V1_STR}/news/{news.id}")
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["id"] == news.id

    # Verify it is deleted
    response_get = await client.get(f"{settings.API_V1_STR}/news/{news.id}")
    assert response_get.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_delete_news_subscription_api_not_found(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    response = await client.delete(f"{settings.API_V1_STR}/news/999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "News subscription not found"
