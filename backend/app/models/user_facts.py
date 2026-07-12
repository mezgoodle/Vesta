from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserFact(Base):
    __tablename__ = "user_facts"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    fact_content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String, nullable=True, default=None)

    # Placeholder for future Level 3 (Vector RAG) embedding column:
    # embedding: Mapped[Optional[Vector]] = mapped_column(Vector(384), nullable=True)

    # Relationship
    user: Mapped["User"] = relationship(back_populates="facts")
