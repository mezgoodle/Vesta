import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.models.device import SmartDevice
from app.schemas.weather import WeatherData


@pytest.fixture
def mock_llm_service():
    with patch("app.api.v1.endpoints.cron.LLMService") as mock_llm_cls:
        mock_service = AsyncMock()
        mock_llm_cls.return_value = mock_service
        yield mock_service


@pytest.fixture
def mock_calendar_service():
    with patch("app.api.v1.endpoints.cron.google_calendar_service_instance") as mock_service:
        yield mock_service


@pytest.fixture
def mock_weather_service():
    with patch("app.api.v1.endpoints.cron.weather_service_instance") as mock_service:
        yield mock_service


@pytest.fixture
def mock_httpx_client():
    with patch("app.api.v1.endpoints.cron.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        yield mock_client


@pytest.mark.asyncio
async def test_cron_endpoints_require_cron_secret(client: AsyncClient) -> None:
    # Test morning digest endpoint fails without secret
    response = await client.post(f"{settings.API_V1_STR}/cron/morning-digest")
    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden: Invalid cron secret"

    # Test check power status endpoint fails without secret
    response = await client.post(f"{settings.API_V1_STR}/cron/check-power-status")
    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden: Invalid cron secret"

    # Test morning digest endpoint fails with wrong secret
    response = await client.post(
        f"{settings.API_V1_STR}/cron/morning-digest",
        headers={"X-Cron-Secret": "wrong-secret-key"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden: Invalid cron secret"


@pytest.mark.asyncio
async def test_morning_digest_success(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_llm_service,
    mock_calendar_service,
    mock_weather_service,
    mock_httpx_client,
) -> None:
    # Create test user in DB
    user = User(
        email="cron-digest-user@example.com",
        hashed_password="hashedpassword",
        telegram_id=98765,
        city_name="Kyiv",
        is_daily_summary_enabled=True,
        google_refresh_token="valid-refresh-token",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Mock calendar events
    event = MagicMock()
    event.start_time = datetime.time(9, 0)
    event.summary = "FastAPI Standup"
    mock_calendar_service.get_today_events = AsyncMock(return_value=[event])

    # Mock weather service
    mock_weather = MagicMock(spec=WeatherData)
    mock_weather.city = "Kyiv"
    mock_weather.temp = 20
    mock_weather.description = "Clear sky"
    mock_weather_service.get_current_weather_by_city_name = AsyncMock(
        return_value=mock_weather
    )

    # Mock LLM service
    mock_llm_service.chat.return_value = "Good morning! FastAPI Standup is at 09:00."

    # Mock Telegram API response
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_httpx_client.post.return_value = mock_response

    # Send POST request with correct header secret
    response = await client.post(
        f"{settings.API_V1_STR}/cron/morning-digest",
        headers={"X-Cron-Secret": settings.CRON_SECRET_KEY},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["sent_digests_count"] == 1

    # Verify calendar call
    mock_calendar_service.get_today_events.assert_called_once_with(
        user.id, db_session
    )

    # Verify LLM call
    mock_llm_service.chat.assert_called_once()

    # Verify Telegram sendMessage post call
    mock_httpx_client.post.assert_called_once()
    kwargs = mock_httpx_client.post.call_args.kwargs
    assert kwargs["data"]["chat_id"] == 98765
    assert kwargs["data"]["text"] == "Good morning! FastAPI Standup is at 09:00."


@pytest.mark.asyncio
async def test_check_power_status_success(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    # Create test user
    user = User(
        email="cron-device-user@example.com",
        hashed_password="hashedpassword",
        telegram_id=45678,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create test devices
    device1 = SmartDevice(
        user_id=user.id,
        name="Living Room Light",
        entity_id="light.living_room",
        device_type="light",
        room="Living Room",
    )
    device2 = SmartDevice(
        user_id=user.id,
        name="Kitchen Smart Plug",
        entity_id="switch.kitchen_plug",
        device_type="switch",
        room="Kitchen",
    )
    db_session.add_all([device1, device2])
    await db_session.commit()

    # Send POST request with correct header secret
    response = await client.post(
        f"{settings.API_V1_STR}/cron/check-power-status",
        headers={"X-Cron-Secret": settings.CRON_SECRET_KEY},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["checked_devices_count"] == 2
    
    devices = data["devices"]
    assert len(devices) == 2
    assert devices[0]["name"] == "Living Room Light"
    assert devices[0]["state"] == "on"
    assert devices[0]["status"] == "online"
    assert devices[1]["name"] == "Kitchen Smart Plug"
