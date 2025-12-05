import pytest
from app.core.config import settings
from app.crud.crud_user import user as crud_user
from app.schemas.user import UserCreate
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_device_api(client: AsyncClient, db_session: AsyncSession) -> None:
    user_in = UserCreate(
        telegram_id=404040404, full_name="Device API User", username="deviceapi"
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    device_data = {
        "name": "API Light",
        "entity_id": "light.api",
        "device_type": "light",
        "room": "API Room",
        "user_id": user.id,
    }
    response = await client.post(f"{settings.API_V1_STR}/devices/", json=device_data)
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == device_data["name"]
    assert content["user_id"] == user.id


@pytest.mark.asyncio
async def test_read_devices_api(client: AsyncClient, db_session: AsyncSession) -> None:
    response = await client.get(f"{settings.API_V1_STR}/devices/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
