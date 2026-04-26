import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.chat import ChatHistory
from app.schemas.calendar import CalendarEventCreate
from app.services.llm import LLMService


@pytest.fixture
def mock_genai_client():
    with patch("app.services.llm.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        # Mock the aio property which handles async calls
        mock_client.aio = MagicMock()
        mock_client.aio.models = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock()
        yield mock_client


@pytest.fixture
def mock_settings():
    with patch("app.services.llm.settings") as mock_settings:
        mock_settings.GOOGLE_API_KEY = "test_api_key"
        mock_settings.GOOGLE_MODEL_NAME = "gemini-test"
        mock_settings.SYSTEM_INSTRUCTION = "Test Instruction"
        yield mock_settings


@pytest.fixture
def llm_service(mock_settings, mock_genai_client):
    return LLMService()


def _extract_tool(mock_genai_client, tool_name):
    kwargs = mock_genai_client.aio.models.generate_content.call_args.kwargs
    tools = kwargs["config"].tools
    return next(t for t in tools if t.__name__ == tool_name)


@pytest.mark.asyncio
async def test_chat_basic_flow(llm_service, mock_genai_client):
    # Mock response
    mock_response = MagicMock()
    mock_response.text = "Hello, world!"
    mock_response.usage_metadata = MagicMock()
    mock_genai_client.aio.models.generate_content.return_value = mock_response

    db_session = AsyncMock()
    history = [
        ChatHistory(role="user", content="Hi"),
        ChatHistory(role="assistant", content="Hello"),
    ]

    response = await llm_service.chat("How are you?", history, 123, db_session)

    assert response == "Hello, world!"

    # Verify generate_content called
    mock_genai_client.aio.models.generate_content.assert_called_once()
    kwargs = mock_genai_client.aio.models.generate_content.call_args.kwargs
    assert kwargs["model"] == "gemini-test"
    assert len(kwargs["contents"]) == 3  # 2 history + 1 new message
    assert kwargs["contents"][-1].parts[0].text == "How are you?"


@pytest.mark.asyncio
async def test_chat_extract_and_run_weather_tool(llm_service, mock_genai_client):
    mock_response = MagicMock()
    mock_response.text = "Weather response"
    mock_genai_client.aio.models.generate_content.return_value = mock_response

    db_session = AsyncMock()
    await llm_service.chat("Weather in London", [], 123, db_session)

    weather_tool = _extract_tool(mock_genai_client, "get_weather_info")

    # Mock OpenMeteoService
    with patch("app.services.llm.OpenMeteoService") as MockOpenMeteoService:
        mock_meteo_service = AsyncMock()
        MockOpenMeteoService.return_value = mock_meteo_service

        mock_weather_data = MagicMock()
        mock_weather_data.city_name = "London"
        mock_weather_data.current_temp = 20.0
        mock_weather_data.current_conditions = "Sunny"
        
        forecast = MagicMock()
        forecast.date = "2025-01-01"
        forecast.max_temp = 25.0
        forecast.min_temp = 15.0
        forecast.precipitation_prob_max = 10
        mock_weather_data.daily_forecasts = [forecast]
        
        mock_meteo_service.get_weather.return_value = mock_weather_data

        # Run the tool
        result = await weather_tool(city="London", days=7)

        assert "London" in result
        assert "20.0" in result
        assert "25.0" in result

        mock_meteo_service.get_weather.assert_called_with(
            city="London", days=7
        )
        mock_meteo_service.close.assert_called_once()


@pytest.mark.asyncio
async def test_chat_extract_and_run_calendar_events_tool(
    llm_service, mock_genai_client
):
    mock_response = MagicMock()
    mock_response.text = "Calendar response"
    mock_genai_client.aio.models.generate_content.return_value = mock_response

    db_session = AsyncMock()
    await llm_service.chat("My events", [], 123, db_session)

    calendar_tool = _extract_tool(mock_genai_client, "get_calendar_events")

    with patch("app.services.llm.GoogleCalendarService") as MockCalendarService:
        mock_calendar_service = MockCalendarService.return_value
        mock_calendar_service.get_upcoming_events = AsyncMock()

        # Mock events
        event1 = MagicMock()
        event1.summary = "Meeting"
        event1.start_time = datetime.datetime(2025, 1, 1, 10, 0)
        event1.location = "Room A"
        event1.description = "Test meeting"

        mock_calendar_service.get_upcoming_events.return_value = [event1]

        result = await calendar_tool(days=7)

        assert "Meeting" in result
        assert "Room A" in result

        mock_calendar_service.get_upcoming_events.assert_called_with(
            user_id=123, db=db_session, days=7
        )


@pytest.mark.asyncio
async def test_chat_extract_and_run_schedule_event_tool(llm_service, mock_genai_client):
    mock_response = MagicMock()
    mock_response.text = "Schedule response"
    mock_genai_client.aio.models.generate_content.return_value = mock_response

    db_session = AsyncMock()
    await llm_service.chat("Schedule event", [], 123, db_session)

    schedule_tool = _extract_tool(mock_genai_client, "schedule_event_tool")

    with patch("app.services.llm.GoogleCalendarService") as MockCalendarService:
        mock_calendar_service = MockCalendarService.return_value
        mock_calendar_service.create_event = AsyncMock()

        mock_calendar_service.create_event.return_value = {
            "html_link": "http://event.link",
            "start_time": datetime.datetime(2025, 1, 1, 10, 0),
            "end_time": datetime.datetime(2025, 1, 1, 11, 0),
        }

        result = await schedule_tool(
            summary="New Event",
            start_time_iso="2025-01-01T10:00:00",
            duration_minutes=60,
            description="Notes",
        )

        assert "successfully created" in result
        assert "http://event.link" in result

        mock_calendar_service.create_event.assert_called_once()
        call_kwargs = mock_calendar_service.create_event.call_args.kwargs
        assert call_kwargs["user_id"] == 123
        assert call_kwargs["db"] == db_session
        assert isinstance(call_kwargs["event_data"], CalendarEventCreate)
        assert call_kwargs["event_data"].summary == "New Event"


@pytest.mark.asyncio
async def test_schedule_event_tool_invalid_date(llm_service, mock_genai_client):
    mock_response = MagicMock()
    mock_response.text = "Response"
    mock_genai_client.aio.models.generate_content.return_value = mock_response

    db_session = AsyncMock()
    await llm_service.chat("Schedule", [], 123, db_session)

    schedule_tool = _extract_tool(mock_genai_client, "schedule_event_tool")

    result = await schedule_tool(summary="Test", start_time_iso="invalid-date")
    assert "Invalid datetime format" in result


@pytest.mark.asyncio
async def test_generate_session_summary(llm_service, mock_genai_client):
    """Test that generate_session_summary returns the LLM response text."""
    mock_response = MagicMock()
    mock_response.text = "User discussed Python async patterns and SQLAlchemy."
    mock_genai_client.aio.models.generate_content.return_value = mock_response

    messages = [
        ChatHistory(role="user", content="How does asyncio work?"),
        ChatHistory(role="model", content="Asyncio is Python's async framework."),
    ]

    result = await llm_service.generate_session_summary(
        current_summary=None,
        recent_messages=messages,
    )

    assert result == "User discussed Python async patterns and SQLAlchemy."
    mock_genai_client.aio.models.generate_content.assert_called_once()
    call_kwargs = mock_genai_client.aio.models.generate_content.call_args.kwargs
    # Should NOT pass tools (plain generate call)
    assert "config" not in call_kwargs
    # Prompt should reference both the current summary placeholder and messages
    contents = call_kwargs["contents"]
    assert "No previous summary" in contents
    assert "How does asyncio work?" in contents


@pytest.mark.asyncio
async def test_generate_session_summary_with_existing_summary(
    llm_service, mock_genai_client
):
    """Test that the existing summary is folded into the prompt."""
    mock_response = MagicMock()
    mock_response.text = "Updated summary."
    mock_genai_client.aio.models.generate_content.return_value = mock_response

    result = await llm_service.generate_session_summary(
        current_summary="User likes Python.",
        recent_messages=[ChatHistory(role="user", content="Tell me about FastAPI.")],
    )

    assert result == "Updated summary."
    contents = mock_genai_client.aio.models.generate_content.call_args.kwargs[
        "contents"
    ]
    assert "User likes Python." in contents
    assert "Tell me about FastAPI." in contents


@pytest.mark.asyncio
async def test_generate_session_summary_api_error_returns_fallback(
    llm_service, mock_genai_client
):
    """On API failure, generate_session_summary should return the current summary."""
    mock_genai_client.aio.models.generate_content.side_effect = Exception("API error")

    result = await llm_service.generate_session_summary(
        current_summary="Existing summary text.",
        recent_messages=[ChatHistory(role="user", content="Hello")],
    )

    assert result == "Existing summary text."


@pytest.mark.asyncio
async def test_chat_injects_session_summary_into_system_instruction(
    llm_service, mock_genai_client
):
    """Test that a non-None session_summary appears in the system instruction."""
    mock_response = MagicMock()
    mock_response.text = "response text"
    mock_response.usage_metadata = None
    mock_genai_client.aio.models.generate_content.return_value = mock_response

    db_session = MagicMock()
    await llm_service.chat(
        "Hello",
        [],
        123,
        db_session,
        session_summary="User previously asked about the weather.",
    )

    kwargs = mock_genai_client.aio.models.generate_content.call_args.kwargs
    system_instruction = kwargs["config"].system_instruction
    assert "CONVERSATION SUMMARY" in system_instruction
    assert "User previously asked about the weather." in system_instruction
