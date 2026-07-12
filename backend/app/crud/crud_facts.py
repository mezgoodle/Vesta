from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.user_facts import UserFact
from app.schemas.user_facts import FactCreate, FactUpdate


class CRUDUserFact(CRUDBase[UserFact, FactCreate, FactUpdate]):
    async def get(self, *args, **kwargs):
        raise NotImplementedError("Use tenant-scoped methods instead")

    async def get_multi(self, *args, **kwargs):
        raise NotImplementedError("Use tenant-scoped methods instead")

    async def update(self, *args, **kwargs):
        raise NotImplementedError("Use tenant-scoped methods instead")

    async def remove(self, *args, **kwargs):
        raise NotImplementedError("Use tenant-scoped methods instead")

    async def get_by_user_id(
        self, db: AsyncSession, *, user_id: int, limit: int = 100
    ) -> list[UserFact]:
        """Fetch facts for a specific user up to a limit, ensuring strict multi-tenant isolation."""
        result = await db.execute(
            select(UserFact)
            .filter(UserFact.user_id == user_id)
            .order_by(UserFact.created_at.desc(), UserFact.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_fact(
        self, db: AsyncSession, *, user_id: int, obj_in: FactCreate
    ) -> UserFact:
        """Create a new fact for a specific user."""
        db_obj = UserFact(
            user_id=user_id,
            fact_content=obj_in.fact_content,
            category=obj_in.category,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete_fact(
        self, db: AsyncSession, *, fact_id: int, user_id: int
    ) -> UserFact | None:
        """Delete a fact, verifying ownership first to ensure multi-tenant isolation."""
        result = await db.execute(
            select(UserFact).filter(UserFact.id == fact_id, UserFact.user_id == user_id)
        )
        db_obj = result.scalars().first()
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
            return db_obj
        return None


user_fact = CRUDUserFact(UserFact)
