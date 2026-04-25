from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.chat import ChatSession
from app.schemas.chat import ChatSessionCreate, ChatSessionUpdate


class CRUDChatSession(CRUDBase[ChatSession, ChatSessionCreate, ChatSessionUpdate]):
    async def get(self, db: AsyncSession, id: int) -> ChatSession | None:  # type: ignore[override]
        result = await db.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .filter(ChatSession.id == id)
        )
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[ChatSession]:
        result = await db.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_user_id(
        self, db: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[ChatSession]:
        result = await db.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.created_at.desc(), ChatSession.id.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


chat_session = CRUDChatSession(ChatSession)
