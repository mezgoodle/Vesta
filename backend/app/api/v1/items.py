"""
Items API routes.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_items():
    """Get all items."""
    return {"items": []}


@router.get("/{item_id}")
async def get_item(item_id: int):
    """Get a specific item by ID."""
    return {"item_id": item_id, "name": f"Item {item_id}"}


@router.post("/")
async def create_item(item_data: dict):
    """Create a new item."""
    return {"message": "Item created", "data": item_data}


@router.put("/{item_id}")
async def update_item(item_id: int, item_data: dict):
    """Update an existing item."""
    return {"message": f"Item {item_id} updated", "data": item_data}


@router.delete("/{item_id}")
async def delete_item(item_id: int):
    """Delete an item."""
    return {"message": f"Item {item_id} deleted"}
