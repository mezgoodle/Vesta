from fastapi import APIRouter

from . import auth, items, users

api_router = APIRouter()


api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

api_router.include_router(items.router, prefix="/items", tags=["items"])

api_router.include_router(users.router, prefix="/users", tags=["users"])


@api_router.get("/")
async def api_root() -> dict[str, str | dict]:
    return {
        "message": "Welcome to Vesta API",
        "version": "1.0.0",
        "endpoints": {"auth": "/auth", "items": "/items", "users": "/users"},
    }


@api_router.get("/status")
async def api_status() -> dict[str, str]:
    return {"status": "active", "message": "All API services are running"}
