from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class ChatHistory(Base):
    __tablename__ = "chat_history"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_session.id"))

    user: Mapped["User"] = relationship(back_populates="chat_history")
    session: Mapped["ChatSession"] = relationship(back_populates="messages")


class ChatSession(Base):
    __tablename__ = "chat_session"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String, default="New Chat")

    user: Mapped["User"] = relationship(back_populates="sessions")
    messages: Mapped[list["ChatHistory"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
