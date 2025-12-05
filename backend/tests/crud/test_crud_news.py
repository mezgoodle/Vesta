from datetime import time

import pytest
from app.crud.crud_news import news as crud_news
from app.crud.crud_user import user as crud_user
from app.schemas.news import NewsSubscriptionCreate
from app.schemas.user import UserCreate
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_news_subscription(db_session: AsyncSession) -> None:
    user_in = UserCreate(
        telegram_id=666777888, full_name="News User", username="newsuser"
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    news_in = NewsSubscriptionCreate(
        topic="Technology",
        schedule_time=time(hour=9, minute=0),
        is_active=True,
        user_id=user.id,
    )
    subscription = await crud_news.create(db_session, obj_in=news_in)

    assert subscription.topic == "Technology"
    assert subscription.user_id == user.id


@pytest.mark.asyncio
async def test_get_news_by_user_id(db_session: AsyncSession) -> None:
    user_in = UserCreate(
        telegram_id=777888999, full_name="News List User", username="newslist"
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    news_in = NewsSubscriptionCreate(
        topic="Science",
        schedule_time=time(hour=10, minute=30),
        is_active=True,
        user_id=user.id,
    )
    await crud_news.create(db_session, obj_in=news_in)

    subscriptions = await crud_news.get_by_user_id(db_session, user_id=user.id)
    assert len(subscriptions) == 1
    assert subscriptions[0].topic == "Science"
