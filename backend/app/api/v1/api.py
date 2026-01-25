from fastapi import APIRouter

from app.api.v1.endpoints import chat, devices, google_auth, login, news, users, weather

api_router = APIRouter()
api_router.include_router(login.router, prefix="/login", tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(weather.router, prefix="/weather", tags=["weather"])
api_router.include_router(
    google_auth.router, prefix="/google-auth", tags=["google-auth"]
)
