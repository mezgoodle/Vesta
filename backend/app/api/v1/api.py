from fastapi import APIRouter

from app.api.v1.endpoints import (
    calendar,
    chat,
    devices,
    google_auth,
    knowledge,
    login,
    news,
    sessions,
    tts,
    users,
    weather,
)

api_router = APIRouter()
api_router.include_router(login.router, prefix="/login", tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(weather.router, prefix="/weather", tags=["weather"])
api_router.include_router(
    google_auth.router, prefix="/google-auth", tags=["google-auth"]
)
api_router.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
api_router.include_router(tts.router, prefix="/tts", tags=["tts"])
