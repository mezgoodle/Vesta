
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from app.services.llm import LLMService
from app.models.chat import ChatHistory
from app.core.config import settings

@pytest.fixture
def mock_genai_client():
    with patch("app.services.llm.genai.Client") as mock:
        client_instance = mock.return_value
        # Mock the async generate_content method
        client_instance.aio.models.generate_content = AsyncMock()
        yield mock

@pytest.fixture
def llm_service(mock_genai_client):
    # Ensure settings are valid for initialization
    with patch.object(settings, "GOOGLE_API_KEY", "test_key"), \
         patch.object(settings, "GOOGLE_MODEL_NAME", "gemini-pro"):
        service = LLMService()
        yield service
        service.close()

@pytest.mark.asyncio
async def test_llm_service_initialization():
    """Test successful initialization of LLMService."""
    with patch.object(settings, "GOOGLE_API_KEY", "test_key"), \
         patch.object(settings, "GOOGLE_MODEL_NAME", "gemini-pro"), \
         patch("app.services.llm.genai.Client") as mock_client:

        service = LLMService()
        assert service.client is not None
        assert service.model == "gemini-pro"
        mock_client.assert_called_with(api_key="test_key")

@pytest.mark.asyncio
async def test_llm_service_init_missing_api_key():
    """Test initialization fails without API key."""
    with patch.object(settings, "GOOGLE_API_KEY", ""), \
         patch.object(settings, "GOOGLE_MODEL_NAME", "gemini-pro"):
        with pytest.raises(ValueError, match="GOOGLE_API_KEY is not set"):
            LLMService()

@pytest.mark.asyncio
async def test_llm_service_init_missing_model_name():
    """Test initialization fails without model name."""
    with patch.object(settings, "GOOGLE_API_KEY", "test_key"), \
         patch.object(settings, "GOOGLE_MODEL_NAME", ""):
        with pytest.raises(ValueError, match="GOOGLE_MODEL_NAME is not set"):
            LLMService()

@pytest.mark.asyncio
async def test_chat_success(llm_service):
    """Test successful chat interaction."""
    mock_response = MagicMock()
    mock_response.text = "Hello! How can I help?"
    mock_response.usage_metadata = MagicMock(
        prompt_token_count=10,
        candidates_token_count=20,
        total_token_count=30
    )
    llm_service.client.aio.models.generate_content.return_value = mock_response

    history = [
        ChatHistory(role="user", content="Hi"),
        ChatHistory(role="model", content="Hello")
    ]

    response = await llm_service.chat("How are you?", history, user_id=1, db=AsyncMock())

    assert response == "Hello! How can I help?"
    llm_service.client.aio.models.generate_content.assert_called_once()

    # Verify call arguments
    call_args = llm_service.client.aio.models.generate_content.call_args
    kwargs = call_args.kwargs
    assert kwargs["model"] == "gemini-pro"
    assert len(kwargs["contents"]) == 3  # 2 history + 1 new user message

    # Verify history mapping
    contents = kwargs["contents"]
    assert contents[0].role == "user"
    assert contents[0].parts[0].text == "Hi"
    assert contents[1].role == "model"
    assert contents[1].parts[0].text == "Hello"
    assert contents[2].role == "user"
    assert contents[2].parts[0].text == "How are you?"

@pytest.mark.asyncio
async def test_chat_empty_response(llm_service):
    """Test handling of empty response from LLM."""
    mock_response = MagicMock()
    mock_response.text = None
    llm_service.client.aio.models.generate_content.return_value = mock_response

    response = await llm_service.chat("Hi", [], user_id=1, db=AsyncMock())

    assert response == "I couldn't generate a response. Please try again."

@pytest.mark.asyncio
async def test_chat_api_error(llm_service):
    """Test handling of API errors."""
    llm_service.client.aio.models.generate_content.side_effect = Exception("API Error")

    with pytest.raises(Exception, match="API Error"):
        await llm_service.chat("Hi", [], user_id=1, db=AsyncMock())

@pytest.mark.asyncio
async def test_chat_tools_capture_and_execution(llm_service):
    """
    Test inner tool functions by capturing them from _build_config_with_tools call.
    This effectively tests get_current_weather, get_calendar_events, and schedule_event_tool.
    """
    mock_response = MagicMock()
    mock_response.text = "Response"
    llm_service.client.aio.models.generate_content.return_value = mock_response

    # Spy on _build_config_with_tools to capture the tools
    with patch.object(llm_service, '_build_config_with_tools', wraps=llm_service._build_config_with_tools) as spy_build:
        await llm_service.chat("Test tools", [], user_id=123, db=AsyncMock())

        assert spy_build.called
        tools = spy_build.call_args[1].get('tools') or spy_build.call_args[0][0]

        # Verify tools are present
        tool_names = {t.__name__: t for t in tools}
        assert "get_current_weather" in tool_names
        assert "get_calendar_events" in tool_names
        assert "schedule_event_tool" in tool_names

        # --- Test get_current_weather ---
        get_weather = tool_names["get_current_weather"]

        # Mock WeatherService
        with patch("app.services.llm.WeatherService") as MockWeatherService:
            mock_ws = AsyncMock()
            MockWeatherService.return_value = mock_ws

            # Success case
            mock_data = MagicMock()
            mock_data.city = "London"
            mock_data.description = "rainy"
            mock_data.temp = 15.5
            mock_data.humidity = 80
            mock_data.wind_speed = 5.0
            mock_ws.get_current_weather_by_city_name.return_value = mock_data

            result = await get_weather("London")
            assert "Weather in London" in result
            assert "15.5°C" in result
            assert "rainy" in result

            # Error case
            mock_ws.get_current_weather_by_city_name.side_effect = Exception("Weather Error")
            result_error = await get_weather("Unknown")
            assert "Unable to fetch weather data" in result_error

        # --- Test get_calendar_events ---
        get_events = tool_names["get_calendar_events"]

        # Mock GoogleCalendarService
        with patch("app.services.llm.GoogleCalendarService") as MockCalendarService:
            mock_cs = AsyncMock()
            MockCalendarService.return_value = mock_cs

            # Success case with events
            mock_event = MagicMock()
            mock_event.summary = "Meeting"
            mock_event.start_time = datetime(2023, 10, 1, 10, 0)
            mock_event.location = "Office"
            mock_event.description = "Discuss project"

            mock_cs.get_upcoming_events.return_value = [mock_event]

            result = await get_events(days=7)
            assert "Upcoming events" in result
            assert "Meeting" in result
            assert "Office" in result

            # Success case no events
            mock_cs.get_upcoming_events.return_value = []
            result = await get_events(days=7)
            assert "No events found" in result

            # Error case
            mock_cs.get_upcoming_events.side_effect = Exception("Calendar Error")
            result_error = await get_events(days=7)
            assert "Unable to fetch calendar events" in result_error

        # --- Test schedule_event_tool ---
        schedule_event = tool_names["schedule_event_tool"]

        # Mock GoogleCalendarService again
        with patch("app.services.llm.GoogleCalendarService") as MockCalendarService:
            mock_cs = AsyncMock()
            MockCalendarService.return_value = mock_cs

            # Success case
            mock_created_event = {
                "start_time": datetime(2023, 10, 2, 14, 0),
                "end_time": datetime(2023, 10, 2, 15, 0),
                "html_link": "http://calendar.google.com/event"
            }
            mock_cs.create_event.return_value = mock_created_event

            start_time_iso = "2023-10-02T14:00:00"
            result = await schedule_event("New Meeting", start_time_iso)

            assert "successfully created" in result
            assert "View event" in result

            # Invalid date format
            result_invalid = await schedule_event("Bad Date", "not-a-date")
            assert "Invalid datetime format" in result_invalid

            # Error case during creation
            mock_cs.create_event.side_effect = Exception("Creation Error")
            result_error = await schedule_event("Error Event", start_time_iso)
            assert "Unable to create calendar event" in result_error
