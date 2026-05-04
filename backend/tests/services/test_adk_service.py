"""Tests for the ADK integration service (adk_service.py)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.chat import ChatHistory
from app.services.adk_service import ADKService


@pytest.fixture
def mock_settings():
    with patch("app.services.adk_service.settings") as mock_s:
        mock_s.GOOGLE_API_KEY = "test-key"
        mock_s.GOOGLE_MODEL_NAME = "gemini-test"
        mock_s.SYSTEM_INSTRUCTION = "You are Vesta."
        yield mock_s


@pytest.fixture
def adk_svc(mock_settings):
    return ADKService()


def _make_runner_mock(events_to_yield):
    """
    Helper: build a MagicMock InMemoryRunner that yields the given events
    from run_async and exposes a mock session_service.
    """
    mock_runner = MagicMock()

    # session_service.create_session returns a mock session
    mock_session = MagicMock()
    mock_session.id = "test-session-id"
    mock_session.events = []
    mock_runner.session_service = AsyncMock()
    mock_runner.session_service.create_session = AsyncMock(
        return_value=mock_session
    )
    mock_runner.session_service.append_event = AsyncMock()

    async def mock_run_async(**kwargs):
        for ev in events_to_yield:
            yield ev

    mock_runner.run_async = mock_run_async

    return mock_runner, mock_session


# ------------------------------------------------------------------ #
# process_chat                                                        #
# ------------------------------------------------------------------ #


class TestProcessChat:
    @pytest.mark.asyncio
    async def test_returns_final_response(self, adk_svc):
        """process_chat returns the text from the final event."""
        db = AsyncMock()
        history = [
            ChatHistory(role="user", content="Hi"),
            ChatHistory(role="model", content="Hello!"),
        ]

        # Build a mock event that looks like a final response
        mock_event = MagicMock()
        mock_event.is_final_response.return_value = True
        mock_event.author = "VestaRootAgent"
        mock_part = MagicMock()
        mock_part.text = "I'm doing well, thank you!"
        mock_part.function_call = None
        mock_event.content = MagicMock()
        mock_event.content.parts = [mock_part]

        mock_runner, _ = _make_runner_mock([mock_event])

        with (
            patch("app.services.adk_service.create_tools") as mock_create_tools,
            patch("app.services.adk_service.create_secretary_agent"),
            patch("app.services.adk_service.create_knowledge_agent"),
            patch("app.services.adk_service.create_root_agent") as mock_create_root,
            patch("app.services.adk_service.build_system_instruction"),
            patch("app.services.adk_service.InMemoryRunner", return_value=mock_runner),
        ):
            mock_create_tools.return_value = {
                "secretary": [AsyncMock(), AsyncMock(), AsyncMock()],
                "knowledge": [AsyncMock()],
            }
            # Root agent needs sub_agents for the delegation check
            mock_root = MagicMock()
            mock_root.name = "VestaRootAgent"
            mock_root.sub_agents = []
            mock_create_root.return_value = mock_root

            result = await adk_svc.process_chat(
                user_text="How are you?",
                history_records=history,
                user_id=1,
                db=db,
            )

            assert result == "I'm doing well, thank you!"

    @pytest.mark.asyncio
    async def test_returns_fallback_on_empty_response(self, adk_svc):
        """process_chat returns fallback if no text in events."""
        db = AsyncMock()

        mock_event = MagicMock()
        mock_event.is_final_response.return_value = False
        mock_event.author = "VestaRootAgent"
        mock_event.content = None

        mock_runner, _ = _make_runner_mock([mock_event])

        with (
            patch("app.services.adk_service.create_tools") as mock_ct,
            patch("app.services.adk_service.create_secretary_agent"),
            patch("app.services.adk_service.create_knowledge_agent"),
            patch("app.services.adk_service.create_root_agent") as mock_create_root,
            patch("app.services.adk_service.build_system_instruction"),
            patch("app.services.adk_service.InMemoryRunner", return_value=mock_runner),
        ):
            mock_ct.return_value = {
                "secretary": [],
                "knowledge": [],
            }
            mock_root = MagicMock()
            mock_root.name = "VestaRootAgent"
            mock_root.sub_agents = []
            mock_create_root.return_value = mock_root

            result = await adk_svc.process_chat(
                user_text="Hello", history_records=[], user_id=1, db=db
            )

            assert result == "I couldn't generate a response. Please try again."

    @pytest.mark.asyncio
    async def test_logs_tool_calls(self, adk_svc):
        """process_chat logs function calls from events."""
        db = AsyncMock()

        # Event with a function call
        mock_fc = MagicMock()
        mock_fc.name = "get_weather_info"
        mock_fc.args = {"city": "Kyiv"}

        mock_part_fc = MagicMock()
        mock_part_fc.function_call = mock_fc
        mock_part_fc.text = None

        mock_event_fc = MagicMock()
        mock_event_fc.is_final_response.return_value = False
        mock_event_fc.author = "SecretaryAgent"
        mock_event_fc.content = MagicMock()
        mock_event_fc.content.parts = [mock_part_fc]

        # Final response event
        mock_part_text = MagicMock()
        mock_part_text.text = "Weather is sunny."
        mock_part_text.function_call = None

        mock_event_final = MagicMock()
        mock_event_final.is_final_response.return_value = True
        mock_event_final.author = "VestaRootAgent"
        mock_event_final.content = MagicMock()
        mock_event_final.content.parts = [mock_part_text]

        mock_runner, _ = _make_runner_mock([mock_event_fc, mock_event_final])

        with (
            patch("app.services.adk_service.create_tools") as mock_ct,
            patch("app.services.adk_service.create_secretary_agent"),
            patch("app.services.adk_service.create_knowledge_agent"),
            patch("app.services.adk_service.create_root_agent") as mock_create_root,
            patch("app.services.adk_service.build_system_instruction"),
            patch("app.services.adk_service.InMemoryRunner", return_value=mock_runner),
            patch.object(adk_svc, "_log_function_call") as mock_log_fc,
            patch.object(adk_svc, "_log_agent_delegation") as mock_log_del,
        ):
            mock_ct.return_value = {"secretary": [], "knowledge": []}

            # Provide sub_agents so delegation check works
            mock_secretary = MagicMock()
            mock_secretary.name = "SecretaryAgent"
            mock_knowledge = MagicMock()
            mock_knowledge.name = "KnowledgeAgent"
            mock_root = MagicMock()
            mock_root.name = "VestaRootAgent"
            mock_root.sub_agents = [mock_secretary, mock_knowledge]
            mock_create_root.return_value = mock_root

            result = await adk_svc.process_chat(
                user_text="Weather in Kyiv",
                history_records=[],
                user_id=1,
                db=db,
            )

            assert result == "Weather is sunny."
            mock_log_fc.assert_called_once_with(mock_fc)
            mock_log_del.assert_called_once_with("SecretaryAgent")


# ------------------------------------------------------------------ #
# generate_session_summary                                            #
# ------------------------------------------------------------------ #


class TestGenerateSessionSummary:
    @pytest.mark.asyncio
    async def test_returns_summary_text(self, adk_svc):
        """generate_session_summary returns the agent's response text."""
        messages = [
            ChatHistory(role="user", content="Tell me about Python."),
            ChatHistory(role="model", content="Python is a programming language."),
        ]

        mock_part = MagicMock()
        mock_part.text = "User discussed Python programming."

        mock_event = MagicMock()
        mock_event.is_final_response.return_value = True
        mock_event.content = MagicMock()
        mock_event.content.parts = [mock_part]

        mock_runner, _ = _make_runner_mock([mock_event])

        with (
            patch("app.services.adk_service.create_summary_agent"),
            patch("app.services.adk_service.InMemoryRunner", return_value=mock_runner),
        ):
            result = await adk_svc.generate_session_summary(
                current_summary=None,
                recent_messages=messages,
            )

            assert result == "User discussed Python programming."

    @pytest.mark.asyncio
    async def test_returns_fallback_on_error(self, adk_svc):
        """On error, returns existing summary."""
        with (
            patch(
                "app.services.adk_service.create_summary_agent",
                side_effect=Exception("boom"),
            ),
        ):
            result = await adk_svc.generate_session_summary(
                current_summary="Existing summary.",
                recent_messages=[ChatHistory(role="user", content="Hi")],
            )

            assert result == "Existing summary."

    @pytest.mark.asyncio
    async def test_returns_empty_string_when_no_summary_and_error(self, adk_svc):
        """On error with no existing summary, returns empty string."""
        with (
            patch(
                "app.services.adk_service.create_summary_agent",
                side_effect=Exception("boom"),
            ),
        ):
            result = await adk_svc.generate_session_summary(
                current_summary=None,
                recent_messages=[ChatHistory(role="user", content="Hi")],
            )

            assert result == ""


# ------------------------------------------------------------------ #
# History mapping                                                     #
# ------------------------------------------------------------------ #


class TestMapHistory:
    def test_maps_roles_correctly(self, adk_svc):
        history = [
            ChatHistory(role="user", content="Hello"),
            ChatHistory(role="model", content="Hi there"),
        ]

        result = adk_svc._map_history_to_content(history)

        assert len(result) == 2
        assert result[0].role == "user"
        assert result[0].parts[0].text == "Hello"
        assert result[1].role == "model"
        assert result[1].parts[0].text == "Hi there"

    def test_empty_history(self, adk_svc):
        result = adk_svc._map_history_to_content([])
        assert result == []
