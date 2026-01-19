from app.schemas.base import BaseSchema, BaseSchemaInDB


# Shared properties
class UserBase(BaseSchema):
    telegram_id: int
    full_name: str | None = None
    username: str | None = None
    timezone: str = "UTC"
    is_allowed: bool = False
    email: str | None = None
    is_daily_summary_enabled: bool = False
    is_superuser: bool = False


# Properties to receive on creation
class UserCreate(UserBase):
    password: str | None = None


# Properties to receive on update
class UserUpdate(BaseSchema):
    full_name: str | None = None
    username: str | None = None
    timezone: str | None = None
    password: str | None = None
    is_allowed: bool | None = None
    email: str | None = None
    is_daily_summary_enabled: bool | None = None
    is_superuser: bool | None = None


# Properties for user approval endpoint
class UserApprovalUpdate(BaseSchema):
    is_allowed: bool


# Properties shared by models stored in DB
class UserInDBBase(UserBase, BaseSchemaInDB):
    pass


# Properties to return to client
class User(UserInDBBase):
    pass
