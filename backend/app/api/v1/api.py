from fastapi import APIRouter

from app.api.v1.endpoints import chat, devices, news, users

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
