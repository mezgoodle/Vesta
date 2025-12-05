from app.schemas.base import BaseSchema, BaseSchemaInDB


# Shared properties
class UserBase(BaseSchema):
    telegram_id: int
    full_name: str | None = None
    username: str | None = None
    timezone: str = "UTC"


# Properties to receive on creation
class UserCreate(UserBase):
    pass


# Properties to receive on update
class UserUpdate(BaseSchema):
    full_name: str | None = None
    username: str | None = None
    timezone: str | None = None


# Properties shared by models stored in DB
class UserInDBBase(UserBase, BaseSchemaInDB):
    pass


# Properties to return to client
class User(UserInDBBase):
    pass
