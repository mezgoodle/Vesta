from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, contains_eager

from app.crud.base import CRUDBase
from app.models.chat import ChatHistory, ChatSession
from app.schemas.chat import ChatSessionCreate, ChatSessionUpdate


class CRUDChatSession(CRUDBase[ChatSession, ChatSessionCreate, ChatSessionUpdate]):
    def _base_query(self):
        rn = (
            func.row_number()
            .over(
                partition_by=ChatHistory.session_id,
                order_by=ChatHistory.created_at.desc(),
            )
            .label("rn")
        )
        subq = select(ChatHistory, rn).subquery()
        history_alias = aliased(ChatHistory, subq)
        return (
            select(ChatSession)
            .outerjoin(
                history_alias,
                (ChatSession.id == history_alias.session_id) & (subq.c.rn <= 10),
            )
            .options(contains_eager(ChatSession.messages.of_type(history_alias)))
        )

    async def get(self, db: AsyncSession, id: int) -> ChatSession | None:  # type: ignore[override]
        stmt = self._base_query().filter(ChatSession.id == id)
        result = await db.execute(stmt)
        return result.unique().scalars().first()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[ChatSession]:
        stmt = self._base_query().offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_by_user_id(
        self, db: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[ChatSession]:
        stmt = (
            self._base_query()
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.created_at.desc(), ChatSession.id.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.unique().scalars().all())


chat_session = CRUDChatSession(ChatSession)
