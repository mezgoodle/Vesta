from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
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

    async def get_by_email(self, db: AsyncSession, *, email: str) -> User | None:
        """Get user by email address."""
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    async def authenticate(
        self, db: AsyncSession, *, email: str, password: str
    ) -> User | None:
        """Authenticate a user by email and password."""
        user = await self.get_by_email(db, email=email)
        if not user:
            return None
        if not user.hashed_password:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """Create a new user with hashed password."""
        obj_in_data = obj_in.model_dump(exclude={"password"})
        if obj_in.password:
            obj_in_data["hashed_password"] = get_password_hash(obj_in.password)
        db_obj = User(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


user = CRUDUser(User)
