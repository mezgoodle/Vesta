import pytest
from app.crud.crud_device import device as crud_device
from app.crud.crud_user import user as crud_user
from app.schemas.device import SmartDeviceCreate
from app.schemas.user import UserCreate
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_device(db_session: AsyncSession) -> None:
    user_in = UserCreate(
        telegram_id=444555666, full_name="Device User", username="deviceuser"
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    device_in = SmartDeviceCreate(
        name="Living Room Light",
        entity_id="light.living_room",
        device_type="light",
        room="Living Room",
        user_id=user.id,
    )
    device = await crud_device.create(db_session, obj_in=device_in)

    assert device.name == "Living Room Light"
    assert device.user_id == user.id


@pytest.mark.asyncio
async def test_get_devices_by_user_id(db_session: AsyncSession) -> None:
    user_in = UserCreate(
        telegram_id=555666777, full_name="Device List User", username="devicelist"
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    device_in = SmartDeviceCreate(
        name="Kitchen Switch",
        entity_id="switch.kitchen",
        device_type="switch",
        room="Kitchen",
        user_id=user.id,
    )
    await crud_device.create(db_session, obj_in=device_in)

    devices = await crud_device.get_by_user_id(db_session, user_id=user.id)
    assert len(devices) == 1
    assert devices[0].entity_id == "switch.kitchen"
