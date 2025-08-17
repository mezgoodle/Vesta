from datetime import datetime
from typing import Optional

from passlib.context import CryptContext
from sqlmodel import Field, SQLModel

from app.models.base import BaseModel

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserBase(SQLModel):
    """Base user model with common fields."""

    username: str = Field(index=True, min_length=3, max_length=50, unique=True)
    email: str = Field(index=True, unique=True, min_length=5, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=100)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)


class User(UserBase, BaseModel, table=True):
    """User database model."""

    hashed_password: str


class UserCreate(UserBase):
    """User creation model."""

    password: str = Field(min_length=6, max_length=100)


class UserUpdate(SQLModel):
    """User update model."""

    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    email: Optional[str] = Field(default=None, min_length=5, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = Field(default=None)
    is_superuser: Optional[bool] = Field(default=None)
    password: Optional[str] = Field(default=None, min_length=6, max_length=100)


class UserRead(UserBase):
    """User read model (public response)."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)
