"""Item service for business logic operations."""

from decimal import Decimal

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.item import Item, ItemCreate, ItemUpdate
from app.repositories.item import ItemRepository
from app.services.base import BaseService


class ItemService(BaseService[Item, ItemCreate, ItemUpdate, ItemRepository]):
    """Item service for business logic operations."""

    def __init__(self):
        super().__init__(ItemRepository())

    def get_by_name(self, db: Session, *, name: str) -> list[Item]:
        return self.repository.get_by_name(db, name=name)

    def get_available_items(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[Item]:
        return self.repository.get_available_items(db, skip=skip, limit=limit)

    def get_by_price_range(
        self,
        db: Session,
        *,
        min_price: Decimal,
        max_price: Decimal,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Item]:
        if min_price < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Minimum price cannot be negative",
            )
        if max_price < min_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum price cannot be less than minimum price",
            )
        return self.repository.get_by_price_range(
            db, min_price=min_price, max_price=max_price, skip=skip, limit=limit
        )

    def search_items(
        self, db: Session, *, search_term: str, skip: int = 0, limit: int = 100
    ) -> list[Item]:
        """Search items by name or description."""
        if not search_term or len(search_term.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search term must be at least 2 characters long",
            )
        return self.repository.search_items(
            db, search_term=search_term.strip(), skip=skip, limit=limit
        )

    def get_low_stock_items(
        self, db: Session, *, threshold: int = 10, skip: int = 0, limit: int = 100
    ) -> list[Item]:
        """Get items with low stock."""
        if threshold < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stock threshold cannot be negative",
            )
        return self.repository.get_low_stock_items(
            db, threshold=threshold, skip=skip, limit=limit
        )

    def update_quantity(self, db: Session, *, item_id: int, new_quantity: int) -> Item:
        """Update item quantity with validation."""
        if new_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity cannot be negative",
            )

        item = self.repository.get(db, item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
            )

        return self.repository.update_quantity(
            db, item_id=item_id, new_quantity=new_quantity
        )

    def create(self, db: Session, *, obj_in: ItemCreate) -> Item:
        """Create item with validation."""
        if obj_in.price <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price must be greater than 0",
            )
        if obj_in.quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity cannot be negative",
            )
        return self.repository.create(db, obj_in=obj_in)

    def update(self, db: Session, *, id: int, obj_in: ItemUpdate) -> Item:
        """Update item with validation."""
        item = self.repository.get(db, id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
            )

        if obj_in.price is not None and obj_in.price <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price must be greater than 0",
            )
        if obj_in.quantity is not None and obj_in.quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity cannot be negative",
            )

        return self.repository.update(db, db_obj=item, obj_in=obj_in)
