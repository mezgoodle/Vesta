from app.schemas.base import BaseSchema, BaseSchemaInDB


class SmartDeviceBase(BaseSchema):
    name: str
    entity_id: str
    device_type: str | None = None
    room: str | None = None
    user_id: int


class SmartDeviceCreate(SmartDeviceBase):
    pass


class SmartDeviceUpdate(BaseSchema):
    name: str | None = None
    entity_id: str | None = None
    device_type: str | None = None
    room: str | None = None


class SmartDeviceInDBBase(SmartDeviceBase, BaseSchemaInDB):
    pass


class SmartDevice(SmartDeviceInDBBase):
    pass
