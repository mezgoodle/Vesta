import pytest
from app.core.config import settings
from app.crud.crud_user import user as crud_user
from app.crud.crud_device import device as crud_device
from app.schemas.user import UserCreate
from app.schemas.device import SmartDeviceCreate
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture
async def test_user(db_session: AsyncSession):
    user_in = UserCreate(telegram_id=1234567, full_name="Test User", username="testuser")
    return await crud_user.create(db_session, obj_in=user_in)

@pytest.fixture
async def test_device(db_session: AsyncSession, test_user):
    device_in = SmartDeviceCreate(name="Test Device", entity_id="light.test", device_type="light", room="Test Room", user_id=test_user.id)
    return await crud_device.create(db_session, obj_in=device_in)

@pytest.mark.asyncio
async def test_create_device_api(client: AsyncClient, test_user) -> None:
    device_data = {"name": "API Light", "entity_id": "light.api", "device_type": "light", "room": "API Room", "user_id": test_user.id}
    response = await client.post(f"{settings.API_V1_STR}/devices/", json=device_data)
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == device_data["name"]
    assert content["user_id"] == test_user.id

@pytest.mark.asyncio
async def test_create_device_user_not_found(client: AsyncClient) -> None:
    device_data = {"name": "API Light", "entity_id": "light.api", "device_type": "light", "room": "API Room", "user_id": 999}
    response = await client.post(f"{settings.API_V1_STR}/devices/", json=device_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

@pytest.mark.asyncio
async def test_read_devices_api(client: AsyncClient, test_device) -> None:
    response = await client.get(f"{settings.API_V1_STR}/devices/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

@pytest.mark.asyncio
async def test_read_devices_by_user(client: AsyncClient, test_user, test_device) -> None:
    response = await client.get(f"{settings.API_V1_STR}/devices/?user_id={test_user.id}")
    assert response.status_code == 200
    content = response.json()
    assert isinstance(content, list)
    assert len(content) > 0
    assert content[0]["user_id"] == test_user.id

@pytest.mark.asyncio
async def test_read_device_api(client: AsyncClient, test_device) -> None:
    response = await client.get(f"{settings.API_V1_STR}/devices/{test_device.id}")
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == test_device.id

@pytest.mark.asyncio
async def test_read_device_not_found(client: AsyncClient) -> None:
    response = await client.get(f"{settings.API_V1_STR}/devices/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Device not found"

@pytest.mark.asyncio
async def test_update_device_api(client: AsyncClient, test_device) -> None:
    update_data = {"name": "Updated Device"}
    response = await client.put(f"{settings.API_V1_STR}/devices/{test_device.id}", json=update_data)
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == "Updated Device"

@pytest.mark.asyncio
async def test_update_device_not_found(client: AsyncClient) -> None:
    update_data = {"name": "Updated Device"}
    response = await client.put(f"{settings.API_V1_STR}/devices/999", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Device not found"

@pytest.mark.asyncio
async def test_delete_device_api(client: AsyncClient, test_device) -> None:
    response = await client.delete(f"{settings.API_V1_STR}/devices/{test_device.id}")
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == test_device.id

    response = await client.get(f"{settings.API_V1_STR}/devices/{test_device.id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_device_not_found(client: AsyncClient) -> None:
    response = await client.delete(f"{settings.API_V1_STR}/devices/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Device not found"
