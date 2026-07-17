import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.models.device import SmartDevice
from app.schemas.open_meteo import OpenMeteoResponse, DailyForecast


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
    with patch("app.api.v1.endpoints.cron.open_meteo_service_instance") as mock_service:
        yield mock_service


@pytest.fixture
def mock_gmail_service():
    with patch("app.api.v1.endpoints.cron.gmail_service_instance") as mock_service:
        yield mock_service


@pytest.fixture
def mock_httpx_client():
    with patch("app.api.v1.endpoints.cron.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        yield mock_client


@pytest.fixture
def mock_home_service():
    with patch("app.api.v1.endpoints.cron.HomeAssistantService") as mock_home_cls:
        mock_service = AsyncMock()
        mock_home_cls.return_value = mock_service
        yield mock_service


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

    # Test sync knowledge endpoint fails without secret
    response = await client.post(f"{settings.API_V1_STR}/cron/sync-knowledge")
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
    mock_gmail_service,
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

    # Mock gmail service
    mock_gmail_service.get_emails = AsyncMock(return_value=[])

    # Mock calendar events
    event = MagicMock()
    event.start_time = datetime.time(9, 0)
    event.summary = "FastAPI Standup"
    mock_calendar_service.get_today_events = AsyncMock(return_value=[event])

    # Mock weather service
    mock_weather = MagicMock(spec=OpenMeteoResponse)
    mock_weather.city_name = "Kyiv"
    mock_weather.current_temp = 20.0
    mock_weather.current_conditions = "Clear sky"
    forecast = MagicMock(spec=DailyForecast)
    forecast.max_temp = 25.0
    forecast.min_temp = 15.0
    forecast.precipitation_prob_max = 10
    mock_weather.daily_forecasts = [forecast]
    mock_weather_service.get_weather = AsyncMock(
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
async def test_morning_digest_no_events(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_llm_service,
    mock_calendar_service,
    mock_weather_service,
    mock_gmail_service,
    mock_httpx_client,
) -> None:
    # Create test user in DB
    user = User(
        email="cron-digest-no-events@example.com",
        hashed_password="hashedpassword",
        telegram_id=98765,
        city_name="Kyiv",
        is_daily_summary_enabled=True,
        google_refresh_token="valid-refresh-token",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Mock gmail service
    mock_gmail_service.get_emails = AsyncMock(return_value=[])

    # Mock calendar events to be empty
    mock_calendar_service.get_today_events = AsyncMock(return_value=[])

    # Mock weather service
    mock_weather = MagicMock(spec=OpenMeteoResponse)
    mock_weather.city_name = "Kyiv"
    mock_weather.current_temp = 20.0
    mock_weather.current_conditions = "Clear sky"
    forecast = MagicMock(spec=DailyForecast)
    forecast.max_temp = 25.0
    forecast.min_temp = 15.0
    forecast.precipitation_prob_max = 10
    mock_weather.daily_forecasts = [forecast]
    mock_weather_service.get_weather = AsyncMock(
        return_value=mock_weather
    )

    # Mock LLM service
    mock_llm_service.chat.return_value = "Good morning! No events today."

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
    
    # Verify the prompt contained the "no events" info
    args = mock_llm_service.chat.call_args[0]
    prompt = args[0]
    assert "Сьогодні немає запланованих подій у календарі." in prompt

    # Verify Telegram sendMessage post call
    mock_httpx_client.post.assert_called_once()
    kwargs = mock_httpx_client.post.call_args.kwargs
    assert kwargs["data"]["chat_id"] == 98765
    assert kwargs["data"]["text"] == "Good morning! No events today."


@pytest.mark.asyncio
async def test_morning_digest_with_emails(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_llm_service,
    mock_calendar_service,
    mock_weather_service,
    mock_gmail_service,
    mock_httpx_client,
) -> None:
    # Create test user in DB
    user = User(
        email="cron-digest-emails@example.com",
        hashed_password="hashedpassword",
        telegram_id=98765,
        city_name="Kyiv",
        is_daily_summary_enabled=True,
        google_refresh_token="valid-refresh-token",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Mock gmail service with unread emails
    from app.schemas.gmail import EmailMessage
    email = EmailMessage(
        id="msg123",
        sender="Boss <boss@example.com>",
        subject="Urgent Meeting",
        date="2026-07-14",
        snippet="Please review the budget.",
        body="Please review the budget.",
    )
    mock_gmail_service.get_emails = AsyncMock(return_value=[email])

    # Mock calendar events
    event = MagicMock()
    event.start_time = datetime.time(9, 0)
    event.summary = "FastAPI Standup"
    mock_calendar_service.get_today_events = AsyncMock(return_value=[event])

    # Mock weather service
    mock_weather = MagicMock(spec=OpenMeteoResponse)
    mock_weather.city_name = "Kyiv"
    mock_weather.current_temp = 20.0
    mock_weather.current_conditions = "Clear sky"
    forecast = MagicMock(spec=DailyForecast)
    forecast.max_temp = 25.0
    forecast.min_temp = 15.0
    forecast.precipitation_prob_max = 10
    mock_weather.daily_forecasts = [forecast]
    mock_weather_service.get_weather = AsyncMock(
        return_value=mock_weather
    )

    # Mock LLM service
    mock_llm_service.chat.return_value = "Good morning! You have 1 unread email from Boss."

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

    # Verify gmail call
    mock_gmail_service.get_emails.assert_called_once_with(
        user_id=user.id, db=db_session, query="newer_than:1d", max_results=5
    )

    # Verify LLM call
    mock_llm_service.chat.assert_called_once()
    
    # Verify the prompt contained the email info
    args = mock_llm_service.chat.call_args[0]
    prompt = args[0]
    assert "Urgent Meeting" in prompt
    assert "boss@example.com" in prompt


@pytest.mark.asyncio
async def test_morning_digest_weather_failure(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_llm_service,
    mock_calendar_service,
    mock_weather_service,
    mock_gmail_service,
    mock_httpx_client,
) -> None:
    # Create test user in DB
    user = User(
        email="cron-digest-weather-fail@example.com",
        hashed_password="hashedpassword",
        telegram_id=98765,
        city_name="Kyiv",
        is_daily_summary_enabled=True,
        google_refresh_token="valid-refresh-token",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Mock gmail service
    mock_gmail_service.get_emails = AsyncMock(return_value=[])

    # Mock calendar events
    mock_calendar_service.get_today_events = AsyncMock(return_value=[])

    # Mock weather service to raise exception
    mock_weather_service.get_weather = AsyncMock(
        side_effect=RuntimeError("Weather API connection timed out")
    )

    # Mock LLM service
    mock_llm_service.chat.return_value = "Good morning! Weather is unavailable but you have a good day."

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

    # Verify weather call was attempted
    mock_weather_service.get_weather.assert_called_once_with(
        city=user.city_name, days=1
    )

    # Verify LLM call
    mock_llm_service.chat.assert_called_once()
    
    # Verify the prompt contained the fallback weather message
    args = mock_llm_service.chat.call_args[0]
    prompt = args[0]
    assert "Не вдалося отримати дані про погоду." in prompt


@pytest.mark.asyncio
async def test_check_power_status_success(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_home_service,
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

    # Mock HA get_state calls
    async def mock_get_state(entity_id: str):
        if entity_id == "light.living_room":
            return {"entity_id": entity_id, "state": "on"}
        elif entity_id == "switch.kitchen_plug":
            return {"entity_id": entity_id, "state": "unavailable"}
        return {"state": "unknown"}

    mock_home_service.get_state.side_effect = mock_get_state

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
    assert devices[1]["state"] == "unavailable"
    assert devices[1]["status"] == "offline"

    # Verify home service client was closed
    mock_home_service.close.assert_called_once()


@pytest.mark.asyncio
async def test_check_power_status_partial_failure(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_home_service,
) -> None:
    # Create test user
    user = User(
        email="cron-device-fail-user@example.com",
        hashed_password="hashedpassword",
        telegram_id=11223,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create test devices
    device1 = SmartDevice(
        user_id=user.id,
        name="Failed Device",
        entity_id="light.failed",
        device_type="light",
        room="Living Room",
    )
    device2 = SmartDevice(
        user_id=user.id,
        name="Working Device",
        entity_id="light.working",
        device_type="light",
        room="Kitchen",
    )
    db_session.add_all([device1, device2])
    await db_session.commit()

    # Mock HA get_state calls: first raises exception, second succeeds
    async def mock_get_state(entity_id: str):
        if entity_id == "light.failed":
            raise RuntimeError("HA API Connection Timeout")
        elif entity_id == "light.working":
            return {"entity_id": entity_id, "state": "off"}
        return {"state": "unknown"}

    mock_home_service.get_state.side_effect = mock_get_state

    # Send POST request
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
    # Failed device returns state "unknown" and status "offline"
    assert devices[0]["name"] == "Failed Device"
    assert devices[0]["state"] == "unknown"
    assert devices[0]["status"] == "offline"
    # Working device returns its actual mock state
    assert devices[1]["name"] == "Working Device"
    assert devices[1]["state"] == "off"
    assert devices[1]["status"] == "online"

    # Verify home service client was closed
    mock_home_service.close.assert_called_once()


@pytest.mark.asyncio
async def test_sync_knowledge_success(client: AsyncClient) -> None:
    from app.services.knowledge import knowledge_service
    from app.main import app

    mock_kb = MagicMock()
    mock_kb.sync_with_drive = MagicMock()

    app.dependency_overrides[knowledge_service] = lambda: mock_kb

    try:
        response = await client.post(
            f"{settings.API_V1_STR}/cron/sync-knowledge",
            headers={"X-Cron-Secret": settings.CRON_SECRET_KEY},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "sync started" in data["message"].lower()
        mock_kb.sync_with_drive.assert_called_once()
    finally:
        if knowledge_service in app.dependency_overrides:
            del app.dependency_overrides[knowledge_service]

