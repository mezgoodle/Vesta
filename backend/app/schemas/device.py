from typing import Optional

from app.schemas.base import BaseSchema, BaseSchemaInDB


class SmartDeviceBase(BaseSchema):
    name: str
    entity_id: str
    device_type: Optional[str] = None
    room: Optional[str] = None
    user_id: int


class SmartDeviceCreate(SmartDeviceBase):
    pass


class SmartDeviceUpdate(BaseSchema):
    name: Optional[str] = None
    entity_id: Optional[str] = None
    device_type: Optional[str] = None
    room: Optional[str] = None


class SmartDeviceInDBBase(SmartDeviceBase, BaseSchemaInDB):
    pass


class SmartDevice(SmartDeviceInDBBase):
    pass
