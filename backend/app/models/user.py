from typing import List, Optional

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    timezone: Mapped[str] = mapped_column(String, default="UTC")

    # Relationships
    chat_history: Mapped[List["ChatHistory"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    devices: Mapped[List["SmartDevice"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    news_subscriptions: Mapped[List["NewsSubscription"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
