from typing import List

from app.crud.base import CRUDBase
from app.models.chat import ChatHistory
from app.schemas.chat import ChatHistoryCreate, ChatHistoryUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class CRUDChatHistory(CRUDBase[ChatHistory, ChatHistoryCreate, ChatHistoryUpdate]):
    async def get_by_user_id(
        self, db: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[ChatHistory]:
        result = await db.execute(
            select(ChatHistory)
            .filter(ChatHistory.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


chat = CRUDChatHistory(ChatHistory)
