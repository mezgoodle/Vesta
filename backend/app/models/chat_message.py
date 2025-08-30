import enum
from datetime import datetime
from typing import Optional

from sqlmodel import Column, Enum, Field, SQLModel

from app.models.base import BaseModel


class Role(str, enum.Enum):
    user = "user"
    system = "system"


class ChatMessageBase(SQLModel):
    user_id: str = Field(index=True, nullable=False)
    role: Role = Field(sa_column=Column(Enum(Role), nullable=False))
    content: str = Field(nullable=False)


class ChatMessage(ChatMessageBase, BaseModel, table=True):
    pass


class ChatMessageCreate(ChatMessageBase):
    pass


class ChatMessageRead(ChatMessageBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class ChatMessageUpdate(SQLModel):
    content: Optional[str]
