from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

# Import models to ensure they are registered with Base
from app.models import ChatHistory, NewsSubscription, SmartDevice, User  # noqa: F401
from app.services.home import HomeAssistantService
from app.services.llm import OpenAILLMService

# Global service instances
llm_service = OpenAILLMService()
home_service = HomeAssistantService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up services...")

    # Create tables (for development)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield
    # Shutdown
    print("Shutting down services...")
    await llm_service.close()
    await home_service.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)


# Dependency Injection
def get_llm_service() -> OpenAILLMService:
    return llm_service


def get_home_service() -> HomeAssistantService:
    return home_service


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/test-llm")
async def test_llm(
    prompt: str, service: Annotated[OpenAILLMService, Depends(get_llm_service)]
):
    response = await service.generate_text(prompt)
    return {"response": response}


@app.get("/test-home")
async def test_home(
    entity_id: str, service: Annotated[HomeAssistantService, Depends(get_home_service)]
):
    state = await service.get_state(entity_id)
    return {"state": state}


app.include_router(api_router, prefix=settings.API_V1_STR)
