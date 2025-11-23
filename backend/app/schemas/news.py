from datetime import time
from typing import Optional

from pydantic import BaseModel

from app.schemas.base import BaseSchema, BaseSchemaInDB


class NewsSubscriptionBase(BaseSchema):
    topic: str
    schedule_time: time
    is_active: bool = True
    user_id: int


class NewsSubscriptionCreate(NewsSubscriptionBase):
    pass


class NewsSubscriptionUpdate(BaseSchema):
    topic: Optional[str] = None
    schedule_time: Optional[time] = None
    is_active: Optional[bool] = None


class NewsSubscriptionInDBBase(NewsSubscriptionBase, BaseSchemaInDB):
    pass


class NewsSubscription(NewsSubscriptionInDBBase):
    pass
