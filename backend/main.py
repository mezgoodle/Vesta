"""
FastAPI application main module.
"""

from app.api.v1 import api_router as api_router_v1
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
app.include_router(api_router_v1, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint returning a welcome message."""
    return {"message": "Welcome to Vesta API"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Service is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
