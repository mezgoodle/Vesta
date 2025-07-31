"""User service for business logic operations."""

from typing import Optional

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.user import User, UserCreate, UserUpdate
from app.repositories.user import UserRepository
from app.services.base import BaseService


class UserService(BaseService[User, UserCreate, UserUpdate, UserRepository]):
    """User service for business logic operations."""

    def __init__(self):
        super().__init__(UserRepository())

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Get user by email."""
        return self.repository.get_by_email(db, email=email)

    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """Get user by username."""
        return self.repository.get_by_username(db, username=username)

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """Create user with validation."""
        # Check if user already exists
        user = self.repository.get_by_email(db, email=obj_in.email)
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

        user = self.repository.get_by_username(db, username=obj_in.username)
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this username already exists",
            )

        return self.repository.create(db, obj_in=obj_in)

    def update(self, db: Session, *, id: int, obj_in: UserUpdate) -> User:
        """Update user with validation."""
        user = self.repository.get(db, id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Check email uniqueness if email is being updated
        if obj_in.email and obj_in.email != user.email:
            existing_user = self.repository.get_by_email(db, email=obj_in.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists",
                )

        # Check username uniqueness if username is being updated
        if obj_in.username and obj_in.username != user.username:
            existing_user = self.repository.get_by_username(
                db, username=obj_in.username
            )
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this username already exists",
                )

        return self.repository.update(db, db_obj=user, obj_in=obj_in)

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        """Authenticate user."""
        user = self.repository.authenticate(db, email=email, password=password)
        if not user:
            return None
        if not self.repository.is_active(user):
            return None
        return user

    def is_active(self, user: User) -> bool:
        """Check if user is active."""
        return self.repository.is_active(user)

    def is_superuser(self, user: User) -> bool:
        """Check if user is superuser."""
        return self.repository.is_superuser(user)
