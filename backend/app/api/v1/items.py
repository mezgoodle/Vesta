from decimal import Decimal

from app.core.database import get_session
from app.models.item import ItemCreate, ItemRead, ItemUpdate
from app.services.item import ItemService
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

router = APIRouter()
item_service = ItemService()


@router.post("/", response_model=ItemRead)
def create_item(item_in: ItemCreate, db: Session = Depends(get_session)) -> ItemRead:
    return item_service.create(db, obj_in=item_in)


@router.get("/", response_model=list[ItemRead])
def get_items(
    skip: int = 0,
    limit: int = 100,
    available_only: bool = Query(False, description="Get only available items"),
    db: Session = Depends(get_session),
):
    if available_only:
        return item_service.get_available_items(db, skip=skip, limit=limit)
    return item_service.get_multi(db, skip=skip, limit=limit)


@router.get("/search", response_model=list[ItemRead])
def search_items(
    search_term: str = Query(..., min_length=2, description="Search term"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_session),
):
    return item_service.search_items(
        db, search_term=search_term, skip=skip, limit=limit
    )


@router.get("/price-range", response_model=list[ItemRead])
def get_items_by_price_range(
    min_price: Decimal = Query(..., gt=0, description="Minimum price"),
    max_price: Decimal = Query(..., gt=0, description="Maximum price"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_session),
):
    return item_service.get_by_price_range(
        db, min_price=min_price, max_price=max_price, skip=skip, limit=limit
    )


@router.get("/low-stock", response_model=list[ItemRead])
def get_low_stock_items(
    threshold: int = Query(10, ge=1, description="Stock threshold"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_session),
):
    return item_service.get_low_stock_items(
        db, threshold=threshold, skip=skip, limit=limit
    )


@router.get("/{item_id}", response_model=ItemRead)
def get_item(item_id: int, db: Session = Depends(get_session)):
    item = item_service.get(db, id=item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )
    return item


@router.put("/{item_id}", response_model=ItemRead)
def update_item(item_id: int, item_in: ItemUpdate, db: Session = Depends(get_session)):
    return item_service.update(db, id=item_id, obj_in=item_in)


@router.patch("/{item_id}/quantity", response_model=ItemRead)
def update_item_quantity(
    item_id: int,
    new_quantity: int = Query(..., ge=0, description="New quantity"),
    db: Session = Depends(get_session),
):
    return item_service.update_quantity(db, item_id=item_id, new_quantity=new_quantity)


@router.delete("/{item_id}", response_model=ItemRead)
def delete_item(item_id: int, db: Session = Depends(get_session)):
    item = item_service.delete(db, id=item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )
    return item
