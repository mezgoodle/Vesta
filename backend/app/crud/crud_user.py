from typing import Optional

from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def get_by_telegram_id(
        self, db: AsyncSession, *, telegram_id: int
    ) -> Optional[User]:
        result = await db.execute(select(User).filter(User.telegram_id == telegram_id))
        return result.scalars().first()


user = CRUDUser(User)
