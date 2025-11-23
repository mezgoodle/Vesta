from typing import Any, List

from app import crud
from app.api import deps
from app.crud.crud_user import user as crud_user
from app.schemas.user import User, UserCreate, UserUpdate
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/", response_model=List[User])
async def read_users(
    db: deps.SessionDep,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve users.
    """
    users = await crud_user.get_multi(db, skip=skip, limit=limit)
    return users


@router.post("/", response_model=User)
async def create_user(
    *,
    db: deps.SessionDep,
    user_in: UserCreate,
) -> Any:
    """
    Create new user.
    """
    user = await crud_user.get_by_telegram_id(db, telegram_id=user_in.telegram_id)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this telegram_id already exists in the system.",
        )
    user = await user.create(db, obj_in=user_in)
    return user


@router.get("/{user_id}", response_model=User)
async def read_user(
    *,
    db: deps.SessionDep,
    user_id: int,
) -> Any:
    """
    Get user by ID.
    """
    user = await crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=User)
async def update_user(
    *,
    db: deps.SessionDep,
    user_id: int,
    user_in: UserUpdate,
) -> Any:
    """
    Update a user.
    """
    user = await crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user = await crud_user.update(db, db_obj=user, obj_in=user_in)
    return user


@router.delete("/{user_id}", response_model=User)
async def delete_user(
    *,
    db: deps.SessionDep,
    user_id: int,
) -> Any:
    """
    Delete a user.
    """
    user = await crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user = await crud_user.remove(db, id=user_id)
    return user
