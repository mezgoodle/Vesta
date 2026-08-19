from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import settings
from app.services.archiver import MemoryArchiverService, archiver_service


@pytest.fixture
def archiver():
    return MemoryArchiverService()


def test_archiver_service_dependency():
    instance = archiver_service()
    assert isinstance(instance, MemoryArchiverService)


def test_format_session_to_markdown_structure(archiver: MemoryArchiverService):
    session_data = {
        "id": 42,
        "user_id": 7,
        "title": "Router Setup Chat",
        "summary": "User asked for router credentials.",
        "created_at": "2026-07-29T12:00:00Z",
    }
    messages_data = [
        {"role": "user", "content": "What is my router password?"},
        {"role": "model", "content": "Your router password is 'admin123'."},
    ]

    markdown = archiver.format_session_to_markdown(session_data, messages_data)

    assert "# Chat Session: Router Setup Chat" in markdown
    assert "- **Session ID:** 42" in markdown
    assert "- **User ID:** 7" in markdown
    assert "User asked for router credentials." in markdown
    assert "**user:** What is my router password?" in markdown
    assert "**model:** Your router password is 'admin123'." in markdown


def test_format_session_to_markdown_empty_summary(archiver: MemoryArchiverService):
    session_data = {
        "id": 1,
        "user_id": 1,
        "title": "Quick Question",
        "summary": None,
        "created_at": None,
    }
    messages_data = [{"role": "user", "content": "Hello"}]

    markdown = archiver.format_session_to_markdown(session_data, messages_data)

    assert "No summary available." in markdown
    assert "**user:** Hello" in markdown


@pytest.mark.asyncio
async def test_upload_to_drive_no_folder_id(archiver: MemoryArchiverService):
    with patch.object(settings, "GOOGLE_DRIVE_FOLDER_ID", ""):
        result = await archiver.upload_to_drive("test.md", "content")
        assert result is None


@pytest.mark.asyncio
async def test_upload_to_drive_success(archiver: MemoryArchiverService):
    mock_drive_service = MagicMock()
    mock_files = MagicMock()
    mock_create = MagicMock()

    mock_drive_service.files.return_value = mock_files
    mock_files.create.return_value = mock_create
    mock_create.execute.return_value = {"id": "fake_drive_file_id_123"}

    with (
        patch.object(settings, "GOOGLE_DRIVE_FOLDER_ID", "folder_xyz"),
        patch.object(archiver, "_build_drive_service", return_value=mock_drive_service),
    ):
        file_id = await archiver.upload_to_drive("user_1_session_42.md", "# Test Content")

        assert file_id == "fake_drive_file_id_123"
        mock_files.create.assert_called_once()
        _, kwargs = mock_files.create.call_args
        assert kwargs["body"]["name"] == "user_1_session_42.md"
        assert kwargs["body"]["parents"] == ["folder_xyz"]


@pytest.mark.asyncio
async def test_upload_to_drive_exception_handled(archiver: MemoryArchiverService):
    with (
        patch.object(settings, "GOOGLE_DRIVE_FOLDER_ID", "folder_xyz"),
        patch.object(
            archiver, "_build_drive_service", side_effect=Exception("API Error")
        ),
    ):
        file_id = await archiver.upload_to_drive("test.md", "content")
        assert file_id is None


@pytest.mark.asyncio
async def test_archive_session_full_flow(archiver: MemoryArchiverService):
    session_data = {"id": 10, "user_id": 2, "title": "Test"}
    messages_data = [{"role": "user", "content": "Hi"}]

    with (
        patch.object(settings, "SESSION_ARCHIVE_ENABLED", True),
        patch.object(archiver, "upload_to_drive", new_callable=AsyncMock) as mock_upload,
    ):
        mock_upload.return_value = "file_id_99"
        await archiver.archive_session(session_data, messages_data)

        mock_upload.assert_called_once()
        args = mock_upload.call_args[0]
        assert args[0] == "user_2_session_10.md"
        assert "# Chat Session: Test" in args[1]


@pytest.mark.asyncio
async def test_archive_session_skips_when_disabled(archiver: MemoryArchiverService):
    session_data = {"id": 10, "user_id": 2, "title": "Test"}
    messages_data = [{"role": "user", "content": "Hi"}]

    with (
        patch.object(settings, "SESSION_ARCHIVE_ENABLED", False),
        patch.object(archiver, "upload_to_drive", new_callable=AsyncMock) as mock_upload,
    ):
        await archiver.archive_session(session_data, messages_data)
        mock_upload.assert_not_called()


@pytest.mark.asyncio
async def test_archive_session_skips_when_no_messages(archiver: MemoryArchiverService):
    session_data = {"id": 10, "user_id": 2, "title": "Test"}
    messages_data = []

    with (
        patch.object(settings, "SESSION_ARCHIVE_ENABLED", True),
        patch.object(archiver, "upload_to_drive", new_callable=AsyncMock) as mock_upload,
    ):
        await archiver.archive_session(session_data, messages_data)
        mock_upload.assert_not_called()
