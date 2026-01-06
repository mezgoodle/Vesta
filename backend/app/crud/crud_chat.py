from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.chat import ChatHistory
from app.schemas.chat import ChatHistoryCreate, ChatHistoryUpdate


class CRUDChatHistory(CRUDBase[ChatHistory, ChatHistoryCreate, ChatHistoryUpdate]):
    async def get_by_user_id(
        self, db: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[ChatHistory]:
        result = await db.execute(
            select(ChatHistory)
            .filter(ChatHistory.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_recent_by_user_id(
        self, db: AsyncSession, *, user_id: int, limit: int = 20
    ) -> list[ChatHistory]:
        """
        Get the most recent chat messages for a user, ordered oldest to newest.

        Args:
            db: Database session
            user_id: User ID to fetch messages for
            limit: Maximum number of messages to fetch (default: 20)

        Returns:
            List of ChatHistory records, ordered from oldest to newest
        """
        result = await db.execute(
            select(ChatHistory)
            .filter(ChatHistory.user_id == user_id)
            .order_by(ChatHistory.created_at.desc(), ChatHistory.id.desc())
            .limit(limit)
        )
        # Reverse to get oldest to newest
        return list(reversed(result.scalars().all()))


chat = CRUDChatHistory(ChatHistory)
