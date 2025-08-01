"""User repository for database operations."""

from typing import Optional

from sqlmodel import Session, select

from app.models.user import (
    User,
    UserCreate,
    UserUpdate,
    get_password_hash,
    verify_password,
)
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """User repository for database operations."""

    def __init__(self) -> None:
        super().__init__(User)

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Get user by email."""
        statement = select(User).where(User.email == email)
        return db.exec(statement).first()

    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """Get user by username."""
        statement = select(User).where(User.username == username)
        return db.exec(statement).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        if self.get_by_email(db, email=obj_in.email):
            raise ValueError("Email already registered")
        if self.get_by_username(db, username=obj_in.username):
            raise ValueError("Username already taken")
        db_obj = User(
            username=obj_in.username,
            email=obj_in.email,
            full_name=obj_in.full_name,
            hashed_password=get_password_hash(obj_in.password),
            is_active=obj_in.is_active,
            is_superuser=obj_in.is_superuser,
        )
        db.add(db_obj)
        try:
            db.commit()
            db.refresh(db_obj)
        except Exception as e:
            db.rollback()
            raise RuntimeError(f"Error creating user: {e}") from e
        return db_obj

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        """Check if user is active."""
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        """Check if user is superuser."""
        return user.is_superuser
