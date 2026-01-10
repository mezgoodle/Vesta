import logging
import time
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logger import setup_logging

# Import models to ensure they are registered with Base
from app.models import ChatHistory, NewsSubscription, SmartDevice, User  # noqa: F401
from app.services.home import HomeAssistantService

# Global service instances
home_service = HomeAssistantService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    print("Starting up services...")

    yield
    # Shutdown
    print("Shutting down services...")
    await home_service.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.perf_counter()
    status_code = 500
    response = None

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except StarletteHTTPException as http_exc:
        status_code = http_exc.status_code
        response = JSONResponse(
            status_code=status_code, content={"detail": http_exc.detail}
        )
        return response
    except Exception as e:
        logging.error(f"Critical Error: {e}")
        response = JSONResponse(
            status_code=status_code, content={"detail": "Internal Server Error"}
        )
        return response
    finally:
        process_time = time.perf_counter() - start_time

        log_payload = {
            "http_method": request.method,
            "path": request.url.path,
            "status_code": status_code,
            "duration_sec": round(process_time, 4),
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
        }

        logging.info(
            f"{request.method} {request.url.path}",
            extra={"json_fields": log_payload},
        )


def get_home_service() -> HomeAssistantService:
    return home_service


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/test-home")
async def test_home(
    entity_id: str, service: Annotated[HomeAssistantService, Depends(get_home_service)]
):
    state = await service.get_state(entity_id)
    return {"state": state}


app.include_router(api_router, prefix=settings.API_V1_STR)
