from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def get_by_telegram_id(
        self, db: AsyncSession, *, telegram_id: int
    ) -> User | None:
        result = await db.execute(select(User).filter(User.telegram_id == telegram_id))
        return result.scalars().first()

    async def get_allowed_telegram_ids(self, db: AsyncSession) -> list[int]:
        """Get telegram_ids of all allowed users."""
        result = await db.execute(select(User.telegram_id).filter(User.is_allowed))
        return list(result.scalars().all())


user = CRUDUser(User)
