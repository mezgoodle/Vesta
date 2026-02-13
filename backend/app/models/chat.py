from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class ChatRole(StrEnum):
    USER = "user"
    MODEL = "model"


class ChatHistory(Base):
    __tablename__ = "chat_history"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[ChatRole] = mapped_column(
        Enum(ChatRole, values_callable=lambda obj: [e.value for e in obj])
    )
    content: Mapped[str] = mapped_column(Text)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("chat_session.id", ondelete="CASCADE")
    )

    user: Mapped["User"] = relationship(back_populates="chat_history")
    session: Mapped["ChatSession"] = relationship(back_populates="messages")


class ChatSession(Base):
    __tablename__ = "chat_session"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String, default="New Chat")

    user: Mapped["User"] = relationship(back_populates="sessions")
    messages: Mapped[list["ChatHistory"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
