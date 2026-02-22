import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.scheduler import send_daily_digests
from app.models.user import User
from app.schemas.weather import WeatherData


@pytest.fixture
def mock_db_session():
    # We patch the class AsyncSessionLocal where it is used in scheduler.py
    with patch("app.core.scheduler.AsyncSessionLocal") as mock_session_cls:
        mock_session = AsyncMock()
        # Mock the context manager behavior: async with AsyncSessionLocal() as db:
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        mock_session_cls.return_value.__aexit__.return_value = None
        yield mock_session


@pytest.fixture
def mock_llm_service():
    with patch("app.core.scheduler.LLMService") as mock_llm_cls:
        mock_service = AsyncMock()
        mock_llm_cls.return_value = mock_service
        yield mock_service


@pytest.fixture
def mock_calendar_service():
    with patch("app.core.scheduler.google_calendar_service_instance") as mock_service:
        yield mock_service


@pytest.fixture
def mock_weather_service():
    with patch("app.core.scheduler.weather_service_instance") as mock_service:
        yield mock_service


@pytest.fixture
def mock_httpx_client():
    with patch("app.core.scheduler.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        yield mock_client


@pytest.mark.asyncio
async def test_send_daily_digests_success(
    mock_db_session,
    mock_llm_service,
    mock_calendar_service,
    mock_weather_service,
    mock_httpx_client,
):
    # Mock user
    user = MagicMock(spec=User)
    user.id = 1
    user.telegram_id = 12345
    user.city_name = "Kyiv"

    # Mock DB query result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [user]
    mock_db_session.execute.return_value = mock_result

    # Mock calendar events
    event = MagicMock()
    event.start_time = datetime.time(9, 0)
    event.summary = "Standup"
    # Make get_today_events awaitable
    mock_calendar_service.get_today_events = AsyncMock(return_value=[event])

    # Mock weather
    mock_weather = MagicMock(spec=WeatherData)
    mock_weather.city = "Kyiv"
    mock_weather.temp = 20
    mock_weather.description = "Sunny"
    mock_weather_service.get_current_weather_by_city_name = AsyncMock(
        return_value=mock_weather
    )

    # Mock LLM response
    mock_llm_service.chat.return_value = "Good morning! You have a Standup at 09:00."

    # Mock Telegram response
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_httpx_client.post.return_value = mock_response

    await send_daily_digests()

    # Verify DB query
    mock_db_session.execute.assert_called_once()

    # Verify calendar call
    mock_calendar_service.get_today_events.assert_called_once_with(
        user.id, mock_db_session
    )

    # Verify LLM call
    mock_llm_service.chat.assert_called_once()
    args, _ = mock_llm_service.chat.call_args
    assert "Standup" in args[0]

    # Verify Telegram call
    mock_httpx_client.post.assert_called_once()
    kwargs = mock_httpx_client.post.call_args.kwargs
    assert kwargs["data"]["chat_id"] == 12345
    assert kwargs["data"]["text"] == "Good morning! You have a Standup at 09:00."


@pytest.mark.asyncio
async def test_send_daily_digests_no_users(
    mock_db_session, mock_llm_service, mock_calendar_service, mock_httpx_client
):
    # Mock DB query result with no users
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db_session.execute.return_value = mock_result

    await send_daily_digests()

    mock_calendar_service.get_today_events.assert_not_called()
    mock_llm_service.chat.assert_not_called()


@pytest.mark.asyncio
async def test_send_daily_digests_no_events(
    mock_db_session, mock_llm_service, mock_calendar_service, mock_httpx_client
):
    user = MagicMock(spec=User)
    user.id = 1

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [user]
    mock_db_session.execute.return_value = mock_result

    # Mock no events
    mock_calendar_service.get_today_events = AsyncMock(return_value=[])

    await send_daily_digests()

    mock_llm_service.chat.assert_not_called()


@pytest.mark.asyncio
async def test_send_daily_digests_exception_handling(
    mock_db_session, mock_llm_service, mock_calendar_service, mock_httpx_client
):
    user = MagicMock(spec=User)
    user.id = 1

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [user]
    mock_db_session.execute.return_value = mock_result

    # Simulate exception in calendar service
    mock_calendar_service.get_today_events = AsyncMock(
        side_effect=Exception("Calendar Error")
    )

    # Should not raise exception but log it
    await send_daily_digests()

    mock_llm_service.chat.assert_not_called()
