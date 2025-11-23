from typing import Optional

from app.schemas.base import BaseSchema, BaseSchemaInDB


# Shared properties
class UserBase(BaseSchema):
    telegram_id: int
    full_name: Optional[str] = None
    username: Optional[str] = None
    timezone: str = "UTC"


# Properties to receive on creation
class UserCreate(UserBase):
    pass


# Properties to receive on update
class UserUpdate(BaseSchema):
    full_name: Optional[str] = None
    username: Optional[str] = None
    timezone: Optional[str] = None


# Properties shared by models stored in DB
class UserInDBBase(UserBase, BaseSchemaInDB):
    pass


# Properties to return to client
class User(UserInDBBase):
    pass
