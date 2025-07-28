"""
Users API routes.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_users():
    """Get all users."""
    return {"users": []}


@router.get("/{user_id}")
async def get_user(user_id: int):
    """Get a specific user by ID."""
    return {"user_id": user_id, "username": f"user_{user_id}"}


@router.post("/")
async def create_user(user_data: dict):
    """Create a new user."""
    return {"message": "User created", "data": user_data}


@router.put("/{user_id}")
async def update_user(user_id: int, user_data: dict):
    """Update an existing user."""
    return {"message": f"User {user_id} updated", "data": user_data}


@router.delete("/{user_id}")
async def delete_user(user_id: int):
    """Delete a user."""
    return {"message": f"User {user_id} deleted"}
