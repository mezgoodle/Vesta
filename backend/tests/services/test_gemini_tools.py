"""Tests for the extracted Gemini tool functions in gemini_tools.py."""

import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.calendar import CalendarEventCreate
from app.services.gemini_tools import build_system_instruction, create_tools


@pytest.fixture
def tools():
    """Create tools bound to a test user_id and mock db."""
    db = AsyncMock()
    return create_tools(user_id=42, db=db), db


# ------------------------------------------------------------------ #
# Weather tool                                                        #
# ------------------------------------------------------------------ #


class TestGetWeatherInfo:
    @pytest.mark.asyncio
    async def test_success(self, tools):
        tool_groups, _ = tools
        weather_tool = tool_groups["secretary"][0]  # get_weather_info

        with patch(
            "app.services.gemini_tools.OpenMeteoService"
        ) as MockOpenMeteo:
            mock_service = AsyncMock()
            MockOpenMeteo.return_value = mock_service

            mock_weather = MagicMock()
            mock_weather.city_name = "London"
            mock_weather.current_temp = 20.0
            mock_weather.current_conditions = "Sunny"

            forecast = MagicMock()
            forecast.date = "2026-01-01"
            forecast.max_temp = 25.0
            forecast.min_temp = 15.0
            forecast.precipitation_prob_max = 10
            mock_weather.daily_forecasts = [forecast]

            mock_service.get_weather.return_value = mock_weather

            result = await weather_tool(city="London", days=7)

            assert "London" in result
            assert "20.0" in result
            assert "25.0" in result
            mock_service.get_weather.assert_called_with(city="London", days=7)
            mock_service.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_api_error(self, tools):
        tool_groups, _ = tools
        weather_tool = tool_groups["secretary"][0]

        with patch(
            "app.services.gemini_tools.OpenMeteoService"
        ) as MockOpenMeteo:
            mock_service = AsyncMock()
            MockOpenMeteo.return_value = mock_service
            mock_service.get_weather.side_effect = Exception("API down")

            result = await weather_tool(city="London")
            assert "Unable to fetch weather" in result


# ------------------------------------------------------------------ #
# Calendar tools                                                      #
# ------------------------------------------------------------------ #


class TestGetCalendarEvents:
    @pytest.mark.asyncio
    async def test_success(self, tools):
        tool_groups, db = tools
        calendar_tool = tool_groups["secretary"][1]  # get_calendar_events

        with patch(
            "app.services.gemini_tools.GoogleCalendarService"
        ) as MockCal:
            mock_cal = MockCal.return_value
            mock_cal.get_upcoming_events = AsyncMock()

            event = MagicMock()
            event.summary = "Team Meeting"
            event.start_time = datetime.datetime(2026, 1, 1, 10, 0)
            event.location = "Room A"
            event.description = "Weekly sync"

            mock_cal.get_upcoming_events.return_value = [event]

            result = await calendar_tool(days=7)

            assert "Team Meeting" in result
            assert "Room A" in result
            mock_cal.get_upcoming_events.assert_called_with(
                user_id=42, db=db, days=7
            )

    @pytest.mark.asyncio
    async def test_no_events(self, tools):
        tool_groups, _ = tools
        calendar_tool = tool_groups["secretary"][1]

        with patch(
            "app.services.gemini_tools.GoogleCalendarService"
        ) as MockCal:
            mock_cal = MockCal.return_value
            mock_cal.get_upcoming_events = AsyncMock(return_value=[])

            result = await calendar_tool(days=7)
            assert "No events found" in result

    @pytest.mark.asyncio
    async def test_api_error(self, tools):
        tool_groups, _ = tools
        calendar_tool = tool_groups["secretary"][1]

        with patch(
            "app.services.gemini_tools.GoogleCalendarService"
        ) as MockCal:
            mock_cal = MockCal.return_value
            mock_cal.get_upcoming_events = AsyncMock(
                side_effect=Exception("OAuth error")
            )

            result = await calendar_tool(days=7)
            assert "Unable to fetch calendar" in result


class TestScheduleEventTool:
    @pytest.mark.asyncio
    async def test_success(self, tools):
        tool_groups, db = tools
        schedule_tool = tool_groups["secretary"][2]  # schedule_event_tool

        with patch(
            "app.services.gemini_tools.GoogleCalendarService"
        ) as MockCal:
            mock_cal = MockCal.return_value
            mock_cal.create_event = AsyncMock()
            mock_cal.create_event.return_value = {
                "html_link": "http://cal.link/123",
                "start_time": datetime.datetime(2026, 1, 1, 10, 0),
                "end_time": datetime.datetime(2026, 1, 1, 11, 0),
            }

            result = await schedule_tool(
                summary="Standup",
                start_time_iso="2026-01-01T10:00:00",
                duration_minutes=60,
                description="Daily standup",
            )

            assert "successfully created" in result
            assert "http://cal.link/123" in result

            call_kwargs = mock_cal.create_event.call_args.kwargs
            assert call_kwargs["user_id"] == 42
            assert call_kwargs["db"] == db
            assert isinstance(call_kwargs["event_data"], CalendarEventCreate)
            assert call_kwargs["event_data"].summary == "Standup"

    @pytest.mark.asyncio
    async def test_invalid_datetime(self, tools):
        tool_groups, _ = tools
        schedule_tool = tool_groups["secretary"][2]

        result = await schedule_tool(
            summary="Test", start_time_iso="not-a-date"
        )
        assert "Invalid datetime format" in result


# ------------------------------------------------------------------ #
# Knowledge base tool                                                 #
# ------------------------------------------------------------------ #


class TestConsultKnowledgeBase:
    @pytest.mark.asyncio
    async def test_success(self, tools):
        tool_groups, _ = tools
        kb_tool = tool_groups["knowledge"][0]

        with patch(
            "app.services.gemini_tools.KnowledgeService"
        ) as MockKB:
            mock_kb = MockKB.return_value
            mock_kb.query.return_value = "The recipe calls for 2 cups flour."

            result = await kb_tool(query="flour recipe")
            assert "flour" in result

    @pytest.mark.asyncio
    async def test_error(self, tools):
        tool_groups, _ = tools
        kb_tool = tool_groups["knowledge"][0]

        with patch(
            "app.services.gemini_tools.KnowledgeService"
        ) as MockKB:
            mock_kb = MockKB.return_value
            mock_kb.query.side_effect = Exception("Chroma down")

            result = await kb_tool(query="test")
            assert "couldn't search" in result


# ------------------------------------------------------------------ #
# System instruction builder                                          #
# ------------------------------------------------------------------ #


class TestBuildSystemInstruction:
    def test_basic(self):
        with patch("app.services.gemini_tools.settings") as mock_settings:
            mock_settings.SYSTEM_INSTRUCTION = "You are Vesta."

            result = build_system_instruction()

            assert "You are Vesta." in result
            assert "Current Date and Time" in result
            assert "DELEGATION GUIDELINES" in result

    def test_with_session_summary(self):
        with patch("app.services.gemini_tools.settings") as mock_settings:
            mock_settings.SYSTEM_INSTRUCTION = "You are Vesta."

            result = build_system_instruction(
                session_summary="User asked about weather in Kyiv."
            )

            assert "CONVERSATION SUMMARY" in result
            assert "User asked about weather in Kyiv." in result
