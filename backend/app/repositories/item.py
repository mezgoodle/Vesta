"""Item repository for database operations."""

from decimal import Decimal

from sqlmodel import Session, and_, or_, select

from app.models.item import Item, ItemCreate, ItemUpdate
from app.repositories.base import BaseRepository


class ItemRepository(BaseRepository[Item, ItemCreate, ItemUpdate]):
    """Item repository for database operations."""

    def __init__(self):
        super().__init__(Item)

    def get_by_name(self, db: Session, *, name: str) -> list[Item]:
        """Get items by name (case-insensitive search)."""
        statement = select(Item).where(Item.name.ilike(f"%{name}%"))
        return db.exec(statement).all()

    def get_available_items(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[Item]:
        """Get all available items."""
        statement = (
            select(Item)
            .where(and_(Item.is_available, Item.quantity > 0))
            .offset(skip)
            .limit(limit)
        )
        return db.exec(statement).all()

    def get_by_price_range(
        self,
        db: Session,
        *,
        min_price: Decimal,
        max_price: Decimal,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Item]:
        """Get items within price range."""
        statement = (
            select(Item)
            .where(and_(Item.price >= min_price, Item.price <= max_price))
            .offset(skip)
            .limit(limit)
        )
        return db.exec(statement).all()

    def search_items(
        self, db: Session, *, search_term: str, skip: int = 0, limit: int = 100
    ) -> list[Item]:
        """Search items by name or description."""
        statement = (
            select(Item)
            .where(
                or_(
                    Item.name.ilike(f"%{search_term}%"),
                    Item.description.ilike(f"%{search_term}%"),
                )
            )
            .offset(skip)
            .limit(limit)
        )
        return db.exec(statement).all()

    def get_low_stock_items(
        self, db: Session, *, threshold: int = 10, skip: int = 0, limit: int = 100
    ) -> list[Item]:
        """Get items with low stock."""
        statement = (
            select(Item)
            .where(and_(Item.quantity <= threshold, Item.quantity > 0))
            .offset(skip)
            .limit(limit)
        )
        return db.exec(statement).all()

    def update_quantity(self, db: Session, *, item_id: int, new_quantity: int) -> Item:
        """Update item quantity."""
        item = self.get(db, item_id)
        if item:
            item.quantity = new_quantity
            # Auto-update availability based on quantity
            item.is_available = new_quantity > 0
            db.add(item)
            db.commit()
            db.refresh(item)
        return item
