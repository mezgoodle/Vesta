from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.chat import ChatHistory
    from app.models.device import SmartDevice
    from app.models.news import NewsSubscription


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    timezone: Mapped[str] = mapped_column(String, default="UTC")

    # Relationships
    chat_history: Mapped[list["ChatHistory"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    devices: Mapped[list["SmartDevice"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    news_subscriptions: Mapped[list["NewsSubscription"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
