from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel

from app.models.base import BaseModel


class ItemBase(SQLModel):
    name: str = Field(index=True, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    price: Decimal = Field(gt=0, decimal_places=2)
    quantity: int = Field(ge=0, default=0)
    is_available: bool = Field(default=True)


class Item(ItemBase, BaseModel, table=True):
    pass


class ItemCreate(ItemBase):
    pass


class ItemUpdate(SQLModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    price: Optional[Decimal] = Field(default=None, gt=0, decimal_places=2)
    quantity: Optional[int] = Field(default=None, ge=0)
    is_available: Optional[bool] = Field(default=None)


class ItemRead(ItemBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
