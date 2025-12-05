from datetime import time

from app.schemas.base import BaseSchema, BaseSchemaInDB


class NewsSubscriptionBase(BaseSchema):
    topic: str
    schedule_time: time
    is_active: bool = True
    user_id: int


class NewsSubscriptionCreate(NewsSubscriptionBase):
    pass


class NewsSubscriptionUpdate(BaseSchema):
    topic: str | None = None
    schedule_time: time | None = None
    is_active: bool | None = None


class NewsSubscriptionInDBBase(NewsSubscriptionBase, BaseSchemaInDB):
    pass


class NewsSubscription(NewsSubscriptionInDBBase):
    pass
