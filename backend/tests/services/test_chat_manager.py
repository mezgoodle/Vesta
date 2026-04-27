"""Tests for the chat_manager background task worker."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.chat_manager import update_session_summary_task


@pytest.fixture
def mock_db():
    """A mock async context manager simulating AsyncSessionLocal()."""
    db = AsyncMock()
    db.__aenter__ = AsyncMock(return_value=db)
    db.__aexit__ = AsyncMock(return_value=False)
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_update_session_summary_task_happy_path(mock_db):
    """Summary task fetches session + messages, calls LLM, updates and commits."""
    mock_session = MagicMock()
    mock_session.summary = "Old summary."

    mock_messages = [
        MagicMock(role="user", content="Hello"),
        MagicMock(role="model", content="Hi there"),
    ]

    with (
        patch("app.services.chat_manager.AsyncSessionLocal", return_value=mock_db),
        patch(
            "app.services.chat_manager.crud_session.get",
            new_callable=AsyncMock,
            return_value=mock_session,
        ),
        patch(
            "app.services.chat_manager.crud_chat.get_recent_by_session_id",
            new_callable=AsyncMock,
            return_value=mock_messages,
        ),
        patch(
            "app.services.chat_manager.crud_session.update",
            new_callable=AsyncMock,
        ) as mock_update,
        patch("app.services.chat_manager.ADKService") as MockADK,
    ):
        mock_adk_instance = MagicMock()
        mock_adk_instance.generate_session_summary = AsyncMock(
            return_value="New concise summary."
        )
        MockADK.return_value = mock_adk_instance

        await update_session_summary_task(session_id=42)

        # Verify LLM was called with the right args
        mock_adk_instance.generate_session_summary.assert_awaited_once_with(
            current_summary="Old summary.",
            recent_messages=mock_messages,
        )

        # Verify summary was persisted
        mock_update.assert_awaited_once_with(
            mock_db,
            db_obj=mock_session,
            obj_in={"summary": "New concise summary."},
        )
        mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_session_summary_task_session_not_found(mock_db):
    """Task should exit gracefully when session doesn't exist."""
    with (
        patch("app.services.chat_manager.AsyncSessionLocal", return_value=mock_db),
        patch(
            "app.services.chat_manager.crud_session.get",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch("app.services.chat_manager.ADKService") as MockADK,
    ):
        await update_session_summary_task(session_id=999)

        # LLM should never be instantiated
        MockADK.assert_not_called()
        mock_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_session_summary_task_no_messages(mock_db):
    """Task should exit gracefully when there are no messages to summarise."""
    mock_session = MagicMock()
    mock_session.summary = None

    with (
        patch("app.services.chat_manager.AsyncSessionLocal", return_value=mock_db),
        patch(
            "app.services.chat_manager.crud_session.get",
            new_callable=AsyncMock,
            return_value=mock_session,
        ),
        patch(
            "app.services.chat_manager.crud_chat.get_recent_by_session_id",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch("app.services.chat_manager.ADKService") as MockADK,
    ):
        await update_session_summary_task(session_id=42)

        MockADK.assert_not_called()
        mock_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_session_summary_task_llm_error_rolls_back(mock_db):
    """On LLM failure, the DB transaction should be rolled back."""
    mock_session = MagicMock()
    mock_session.summary = "Existing."

    with (
        patch("app.services.chat_manager.AsyncSessionLocal", return_value=mock_db),
        patch(
            "app.services.chat_manager.crud_session.get",
            new_callable=AsyncMock,
            return_value=mock_session,
        ),
        patch(
            "app.services.chat_manager.crud_chat.get_recent_by_session_id",
            new_callable=AsyncMock,
            return_value=[MagicMock(role="user", content="Hi")],
        ),
        patch("app.services.chat_manager.ADKService") as MockADK,
    ):
        mock_adk_instance = MagicMock()
        mock_adk_instance.generate_session_summary = AsyncMock(
            side_effect=Exception("LLM down")
        )
        MockADK.return_value = mock_adk_instance

        await update_session_summary_task(session_id=42)

        mock_db.commit.assert_not_awaited()
        mock_db.rollback.assert_awaited_once()
