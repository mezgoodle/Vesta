from datetime import datetime
from typing import List, Optional

from app.db.base import Base
from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    timezone: Mapped[str] = mapped_column(String, default="UTC")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

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
