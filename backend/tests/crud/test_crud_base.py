import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.crud_user import user as crud_user
from app.crud.crud_device import device as crud_device
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.device import SmartDeviceCreate, SmartDeviceUpdate
from app.crud.base import CRUDBase

@pytest.mark.asyncio
async def test_base_get_multi(db_session: AsyncSession) -> None:
    # Use User as a concrete model to test base methods
    user_in1 = UserCreate(telegram_id=2001)
    user_in2 = UserCreate(telegram_id=2002)

    await crud_user.create(db_session, obj_in=user_in1)
    await crud_user.create(db_session, obj_in=user_in2)

    users = await crud_user.get_multi(db_session, skip=0, limit=10)
    assert len(users) >= 2

@pytest.mark.asyncio
async def test_base_remove(db_session: AsyncSession) -> None:
    user_in = UserCreate(telegram_id=2003)
    user_obj = await crud_user.create(db_session, obj_in=user_in)

    removed = await crud_user.remove(db_session, id=user_obj.id)
    assert removed is not None
    assert removed.id == user_obj.id

    missing = await crud_user.get(db_session, id=user_obj.id)
    assert missing is None

    none_removed = await crud_user.remove(db_session, id=999999)
    assert none_removed is None

@pytest.mark.asyncio
async def test_base_update(db_session: AsyncSession) -> None:
    user_in = UserCreate(telegram_id=2004)
    user = await crud_user.create(db_session, obj_in=user_in)

    device_in = SmartDeviceCreate(user_id=user.id, entity_id="device.123", name="My Device", device_type="mobile")
    device_obj = await crud_device.create(db_session, obj_in=device_in)

    device_update_dict = {"name": "Updated Device"}
    updated_device = await crud_device.update(db_session, db_obj=device_obj, obj_in=device_update_dict)
    assert updated_device.name == "Updated Device"

    device_update_schema = SmartDeviceUpdate(name="Another Name")
    updated_device2 = await crud_device.update(db_session, db_obj=device_obj, obj_in=device_update_schema)
    assert updated_device2.name == "Another Name"
