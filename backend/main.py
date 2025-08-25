from contextlib import asynccontextmanager

from app.api.v1 import api_router as api_router_v1
from app.core.database import create_db_and_tables
from app.core.settings import get_settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    try:
        create_db_and_tables()
    except Exception as e:
        raise RuntimeError(f"Failed to initialize database: {e}") from e
    yield
    # Shutdown


# Create FastAPI instance
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Include API routes
app.include_router(api_router_v1, prefix="/api/v1")


@app.get("/")
async def root() -> dict:
    return {"message": "Welcome to Vesta API"}


@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy", "message": "Service is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
