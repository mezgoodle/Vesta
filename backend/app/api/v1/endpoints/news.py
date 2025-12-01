from typing import Any

from app.api import deps
from app.crud.crud_news import news as crud_news
from app.crud.crud_user import user as crud_user
from app.schemas.news import (
    NewsSubscription,
    NewsSubscriptionCreate,
    NewsSubscriptionUpdate,
)
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/", response_model=list[NewsSubscription])
async def read_news_subscriptions(
    db: deps.SessionDep,
    skip: int = 0,
    limit: int = 100,
    user_id: int | None = None,
) -> Any:
    """
    Retrieve news subscriptions.
    """
    if user_id:
        news = await crud_news.get_by_user_id(
            db, user_id=user_id, skip=skip, limit=limit
        )
    else:
        news = await crud_news.get_multi(db, skip=skip, limit=limit)
    return news


@router.post("/", response_model=NewsSubscription)
async def create_news_subscription(
    *,
    db: deps.SessionDep,
    news_in: NewsSubscriptionCreate,
) -> Any:
    """
    Create new news subscription.
    """
    # Check if user exists
    user = await crud_user.get(db, id=news_in.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    news = await crud_news.create(db, obj_in=news_in)
    return news


@router.get("/{news_id}", response_model=NewsSubscription)
async def read_news_subscription(
    *,
    db: deps.SessionDep,
    news_id: int,
) -> Any:
    """
    Get news subscription by ID.
    """
    news = await crud_news.get(db, id=news_id)
    if not news:
        raise HTTPException(status_code=404, detail="News subscription not found")
    return news


@router.put("/{news_id}", response_model=NewsSubscription)
async def update_news_subscription(
    *,
    db: deps.SessionDep,
    news_id: int,
    news_in: NewsSubscriptionUpdate,
) -> Any:
    """
    Update a news subscription.
    """
    news = await crud_news.get(db, id=news_id)
    if not news:
        raise HTTPException(status_code=404, detail="News subscription not found")
    news = await crud_news.update(db, db_obj=news, obj_in=news_in)
    return news


@router.delete("/{news_id}", response_model=NewsSubscription)
async def delete_news_subscription(
    *,
    db: deps.SessionDep,
    news_id: int,
) -> Any:
    """
    Delete a news subscription.
    """
    news = await crud_news.get(db, id=news_id)
    if not news:
        raise HTTPException(status_code=404, detail="News subscription not found")
    news = await crud_news.remove(db, id=news_id)
    return news
