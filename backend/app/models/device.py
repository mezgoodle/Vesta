from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SmartDevice(Base):
    __tablename__ = "smart_devices"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String)
    entity_id: Mapped[str] = mapped_column(String)
    device_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    room: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="devices")
