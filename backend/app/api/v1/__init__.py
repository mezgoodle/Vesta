"""
API package initialization.
Exports the main API router for use in the main application.
"""

from .routes import api_router

__all__ = ["api_router"]
