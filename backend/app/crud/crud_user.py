from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def get_by_telegram_id(
        self, db: AsyncSession, *, telegram_id: int
    ) -> User | None:
        result = await db.execute(select(User).filter(User.telegram_id == telegram_id))
        return result.scalars().first()

    async def get_allowed_telegram_ids(self, db: AsyncSession) -> list[dict[str, int]]:
        """Get telegram_ids and ids of all allowed users."""
        result = await db.execute(
            select(User.id, User.telegram_id).filter(User.is_allowed)
        )
        return [dict(row) for row in result.mappings().all()]


user = CRUDUser(User)
