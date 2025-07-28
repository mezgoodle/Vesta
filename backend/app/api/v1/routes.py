"""
Main API router that includes all sub-routers.
"""

from fastapi import APIRouter

from . import auth, items, users

# Create main API router
api_router = APIRouter()

# Include sub-routers with their respective prefixes and tags
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

api_router.include_router(items.router, prefix="/items", tags=["items"])

api_router.include_router(users.router, prefix="/users", tags=["users"])


# Optional: Add some general API endpoints
@api_router.get("/")
async def api_root():
    """API root endpoint."""
    return {
        "message": "Welcome to Vesta API",
        "version": "1.0.0",
        "endpoints": {"auth": "/auth", "items": "/items", "users": "/users"},
    }


@api_router.get("/status")
async def api_status():
    """API status endpoint."""
    return {"status": "active", "message": "All API services are running"}
