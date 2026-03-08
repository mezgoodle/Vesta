import pytest
from app.core.config import settings
from app.crud.crud_user import user as crud_user
from app.crud.crud_device import device as crud_device
from app.schemas.user import UserCreate
from app.schemas.device import SmartDeviceCreate
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

@pytest.mark.asyncio
async def test_create_device_api(client: AsyncClient, db_session: AsyncSession) -> None:
    user_in = UserCreate(
        telegram_id=404040404, full_name="Device API User", username="deviceapi"
    )
    user = await crud_user.create(db_session, obj_in=user_in)
    await db_session.commit()

    device_data = {
        "name": "API Light",
        "entity_id": "light.api",
        "device_type": "light",
        "room": "API Room",
        "user_id": user.id,
    }
    response = await client.post(f"{settings.API_V1_STR}/devices/", json=device_data)
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["name"] == device_data["name"]
    assert content["user_id"] == user.id

@pytest.mark.asyncio
async def test_create_device_api_user_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    device_data = {
        "name": "API Light",
        "entity_id": "light.api.not_found",
        "device_type": "light",
        "room": "API Room",
        "user_id": 999999, # Non-existent user
    }
    response = await client.post(f"{settings.API_V1_STR}/devices/", json=device_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"

@pytest.mark.asyncio
async def test_read_devices_api(client: AsyncClient, db_session: AsyncSession) -> None:
    response = await client.get(f"{settings.API_V1_STR}/devices/")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_read_devices_by_user_id_api(client: AsyncClient, db_session: AsyncSession) -> None:
    user_in = UserCreate(
        telegram_id=404040405, full_name="Device Read API User", username="deviceapiread"
    )
    user = await crud_user.create(db_session, obj_in=user_in)
    await db_session.commit()

    device_data1 = SmartDeviceCreate(
        name="API Light 1", entity_id="light.api1", device_type="light", room="API Room", user_id=user.id
    )
    device_data2 = SmartDeviceCreate(
        name="API Light 2", entity_id="light.api2", device_type="light", room="API Room", user_id=user.id
    )
    await crud_device.create(db_session, obj_in=device_data1)
    await crud_device.create(db_session, obj_in=device_data2)
    await db_session.commit()

    response = await client.get(f"{settings.API_V1_STR}/devices/?user_id={user.id}")
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert len(content) == 2
    assert content[0]["user_id"] == user.id
    assert content[1]["user_id"] == user.id

@pytest.mark.asyncio
async def test_read_device_api(client: AsyncClient, db_session: AsyncSession) -> None:
    user_in = UserCreate(
        telegram_id=404040406, full_name="Device Get API User", username="deviceapiget"
    )
    user = await crud_user.create(db_session, obj_in=user_in)
    await db_session.commit()

    device_data = SmartDeviceCreate(
        name="API Switch", entity_id="switch.api", device_type="switch", room="API Room", user_id=user.id
    )
    device = await crud_device.create(db_session, obj_in=device_data)
    await db_session.commit()

    response = await client.get(f"{settings.API_V1_STR}/devices/{device.id}")
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["name"] == "API Switch"
    assert content["id"] == device.id

@pytest.mark.asyncio
async def test_read_device_api_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    response = await client.get(f"{settings.API_V1_STR}/devices/999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Device not found"

@pytest.mark.asyncio
async def test_update_device_api(client: AsyncClient, db_session: AsyncSession) -> None:
    user_in = UserCreate(
        telegram_id=404040407, full_name="Device Put API User", username="deviceapiput"
    )
    user = await crud_user.create(db_session, obj_in=user_in)
    await db_session.commit()

    device_data = SmartDeviceCreate(
        name="API TV", entity_id="media_player.tv", device_type="media_player", room="Living Room", user_id=user.id
    )
    device = await crud_device.create(db_session, obj_in=device_data)
    await db_session.commit()

    update_data = {
        "name": "Updated TV",
        "room": "Bedroom"
    }
    response = await client.put(f"{settings.API_V1_STR}/devices/{device.id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["name"] == "Updated TV"
    assert content["room"] == "Bedroom"

@pytest.mark.asyncio
async def test_update_device_api_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    update_data = {
        "name": "Updated TV"
    }
    response = await client.put(f"{settings.API_V1_STR}/devices/999999", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Device not found"

@pytest.mark.asyncio
async def test_delete_device_api(client: AsyncClient, db_session: AsyncSession) -> None:
    user_in = UserCreate(
        telegram_id=404040408, full_name="Device Delete API User", username="deviceapidel"
    )
    user = await crud_user.create(db_session, obj_in=user_in)
    await db_session.commit()

    device_data = SmartDeviceCreate(
        name="API Delete", entity_id="switch.del", device_type="switch", room="Kitchen", user_id=user.id
    )
    device = await crud_device.create(db_session, obj_in=device_data)
    await db_session.commit()

    response = await client.delete(f"{settings.API_V1_STR}/devices/{device.id}")
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["id"] == device.id

    # Verify it is deleted
    response_get = await client.get(f"{settings.API_V1_STR}/devices/{device.id}")
    assert response_get.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_delete_device_api_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    response = await client.delete(f"{settings.API_V1_STR}/devices/999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Device not found"
