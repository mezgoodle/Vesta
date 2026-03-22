import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.crud.crud_user import user as crud_user
from app.crud.crud_device import device as crud_device
from app.schemas.user import UserCreate
from app.schemas.device import SmartDeviceCreate

@pytest.mark.asyncio
async def test_create_device_user_not_found(client: AsyncClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    device_data = {
        "name": "API Light",
        "entity_id": "light.api",
        "device_type": "light",
        "room": "API Room",
        "user_id": 999999,
    }
    response = await client.post(f"{settings.API_V1_STR}/devices/", json=device_data, headers=headers)
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_read_devices_by_user_id(client: AsyncClient, db_session: AsyncSession, auth_user: dict) -> None:
    headers = auth_user["headers"]
    user = auth_user["user"]

    device_data = SmartDeviceCreate(name="d1", entity_id="e1", device_type="t1", room="r1", user_id=user.id)
    await crud_device.create(db_session, obj_in=device_data)

    response = await client.get(f"{settings.API_V1_STR}/devices/?user_id={user.id}", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1

@pytest.mark.asyncio
async def test_read_device_by_id(client: AsyncClient, db_session: AsyncSession, auth_user: dict) -> None:
    headers = auth_user["headers"]
    user = auth_user["user"]
    device_data = SmartDeviceCreate(name="d1", entity_id="e1", device_type="t1", room="r1", user_id=user.id)
    device = await crud_device.create(db_session, obj_in=device_data)

    response = await client.get(f"{settings.API_V1_STR}/devices/{device.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == device.id

@pytest.mark.asyncio
async def test_read_device_not_found(client: AsyncClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    response = await client.get(f"{settings.API_V1_STR}/devices/999999", headers=headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_device(client: AsyncClient, db_session: AsyncSession, auth_user: dict) -> None:
    headers = auth_user["headers"]
    user = auth_user["user"]
    device_data = SmartDeviceCreate(name="d1", entity_id="e1", device_type="t1", room="r1", user_id=user.id)
    device = await crud_device.create(db_session, obj_in=device_data)

    update_data = {"name": "updated"}
    response = await client.put(f"{settings.API_V1_STR}/devices/{device.id}", json=update_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "updated"

@pytest.mark.asyncio
async def test_update_device_not_found(client: AsyncClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    response = await client.put(f"{settings.API_V1_STR}/devices/999999", json={"name": "updated"}, headers=headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_device(client: AsyncClient, db_session: AsyncSession, auth_user: dict) -> None:
    headers = auth_user["headers"]
    user = auth_user["user"]
    device_data = SmartDeviceCreate(name="d1", entity_id="e1", device_type="t1", room="r1", user_id=user.id)
    device = await crud_device.create(db_session, obj_in=device_data)

    response = await client.delete(f"{settings.API_V1_STR}/devices/{device.id}", headers=headers)
    assert response.status_code == 200

    # Verify deleted
    response = await client.get(f"{settings.API_V1_STR}/devices/{device.id}", headers=headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_device_not_found(client: AsyncClient, auth_user: dict) -> None:
    headers = auth_user["headers"]
    response = await client.delete(f"{settings.API_V1_STR}/devices/999999", headers=headers)
    assert response.status_code == 404
