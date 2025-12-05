from app.crud.base import CRUDBase
from app.models.news import NewsSubscription
from app.schemas.news import NewsSubscriptionCreate, NewsSubscriptionUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class CRUDNewsSubscription(
    CRUDBase[NewsSubscription, NewsSubscriptionCreate, NewsSubscriptionUpdate]
):
    async def get_by_user_id(
        self, db: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[NewsSubscription]:
        result = await db.execute(
            select(NewsSubscription)
            .filter(NewsSubscription.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


news = CRUDNewsSubscription(NewsSubscription)
