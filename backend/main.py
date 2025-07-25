"""
FastAPI application main module.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import API routes
try:
    from app.api.routes import router as api_router
except ImportError:
    api_router = None

# Create FastAPI instance
app = FastAPI(
    title="Vesta API",
    description="A FastAPI application for the Vesta project",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include API routes
if api_router:
    app.include_router(api_router, prefix="/api/v1", tags=["api"])


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q=None):
    return {"item_id": item_id, "q": q}
