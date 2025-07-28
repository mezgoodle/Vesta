"""
Auth API routes.
"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/login")
async def login(credentials: dict):
    """User login endpoint."""
    return {"message": "Login successful", "token": "sample_token"}


@router.post("/logout")
async def logout():
    """User logout endpoint."""
    return {"message": "Logout successful"}


@router.post("/register")
async def register(user_data: dict):
    """User registration endpoint."""
    return {"message": "User registered successfully", "data": user_data}


@router.get("/me")
async def get_current_user():
    """Get current authenticated user."""
    return {"user": "current_user"}
