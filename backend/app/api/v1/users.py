from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.models.user import UserCreate, UserRead, UserUpdate
from app.services.user import UserService

router = APIRouter()
user_service = UserService()


@router.post("/", response_model=UserRead)
def create_user(user_in: UserCreate, db: Session = Depends(get_session)) -> UserRead:
    return user_service.create(db, obj_in=user_in)


@router.get("/", response_model=list[UserRead])
def get_users(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_session)
) -> list[UserRead]:
    """Get multiple users."""
    return user_service.get_multi(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_session)):
    """Get a user by ID."""
    user = user_service.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.put("/{user_id}", response_model=UserRead)
def update_user(user_id: int, user_in: UserUpdate, db: Session = Depends(get_session)):
    """Update a user."""
    return user_service.update(db, id=user_id, obj_in=user_in)


@router.delete("/{user_id}", response_model=UserRead)
def delete_user(user_id: int, db: Session = Depends(get_session)):
    """Delete a user."""
    user = user_service.delete(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.get("/email/{email}", response_model=UserRead)
def get_user_by_email(email: str, db: Session = Depends(get_session)):
    """Get a user by email."""
    user = user_service.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.get("/username/{username}", response_model=UserRead)
def get_user_by_username(username: str, db: Session = Depends(get_session)):
    """Get a user by username."""
    user = user_service.get_by_username(db, username=username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user
