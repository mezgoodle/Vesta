"""
API routes for the application.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/items")
async def get_items():
    """Get all items."""
    return {"items": []}


@router.get("/items/{item_id}")
async def get_item(item_id: int):
    """Get a specific item by ID."""
    return {"item_id": item_id, "name": f"Item {item_id}"}
