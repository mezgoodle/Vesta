from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import settings
from app.services.knowledge import KnowledgeService


@pytest.fixture
def knowledge_service():
    return KnowledgeService()


@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_DRIVE_FOLDER_ID", "test_folder")
    monkeypatch.setattr(settings, "GOOGLE_API_KEY", "test_key")
    monkeypatch.setattr(settings, "GOOGLE_MODEL_NAME", "test_model")
    monkeypatch.setattr(
        settings, "FILE_SEARCH_STORE_DISPLAY_NAME", "vesta-knowledge-base"
    )


@pytest.fixture
def mock_genai_client():
    with patch("app.services.knowledge.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Mock file_search_stores
        mock_store = MagicMock()
        mock_store.display_name = settings.FILE_SEARCH_STORE_DISPLAY_NAME
        mock_store.name = "stores/test-store"

        mock_client.file_search_stores.list.return_value = [mock_store]

        # Mock files
        mock_file1 = MagicMock()
        mock_file1.display_name = "test.txt [drive_id_1]"
        mock_file1.name = "files/file1"
        mock_file1.update_time = "2024-01-01T10:00:00Z"

        mock_client.files.list.return_value = [mock_file1]

        # Mock operations
        mock_op = MagicMock()
        mock_op.done = True
        mock_client.file_search_stores.upload_to_file_search_store.return_value = (
            mock_op
        )

        # Mock aio.models
        mock_aio_models = AsyncMock()
        mock_response = MagicMock()
        mock_response.text = "This is a test response."
        mock_aio_models.generate_content.return_value = mock_response
        mock_client.aio.models = mock_aio_models

        yield mock_client


@pytest.fixture
def mock_drive_service():
    with patch(
        "app.services.knowledge.KnowledgeService._build_drive_service"
    ) as mock_build:
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        yield mock_service


@pytest.mark.asyncio
async def test_query(knowledge_service, mock_settings, mock_genai_client):
    """Test successful query to Gemini File Search."""
    response = await knowledge_service.query("test query")
    assert response == "This is a test response."

    mock_genai_client.aio.models.generate_content.assert_called_once()
    kwargs = mock_genai_client.aio.models.generate_content.call_args.kwargs
    assert kwargs["model"] == "test_model"
    assert "test query" in kwargs["contents"]
    assert len(kwargs["config"].tools) == 1
    tool = kwargs["config"].tools[0]
    if isinstance(tool, dict):
        assert "file_search" in tool
    else:
        assert tool.file_search is not None
        assert tool.file_search.file_search_store_names == ["stores/test-store"]


@pytest.mark.asyncio
async def test_query_no_api_key(knowledge_service, monkeypatch):
    """Test query raises ValueError if API key missing."""
    monkeypatch.setattr(settings, "GOOGLE_API_KEY", "")
    with pytest.raises(ValueError, match="GOOGLE_API_KEY is not set."):
        await knowledge_service.query("test query")


def test_sync_with_drive_incremental(
    knowledge_service, mock_settings, mock_genai_client, mock_drive_service
):
    """Test incremental sync logic (upload new, skip old, delete removed)."""
    with (
        patch("app.services.knowledge.KnowledgeService._list_drive_files") as mock_list,
        patch(
            "app.services.knowledge.KnowledgeService._download_single_file"
        ) as mock_download,
    ):
        mock_list.return_value = [
            {
                "id": "drive_id_1",
                "name": "test.txt",
                "mimeType": "text/plain",
                "modifiedTime": "2024-01-01T09:00:00Z",
            },  # older, no update needed
            {
                "id": "drive_id_2",
                "name": "new.txt",
                "mimeType": "text/plain",
                "modifiedTime": "2024-01-01T10:00:00Z",
            },  # new file, needs upload
        ]

        mock_download.return_value = (b"content", "new.txt")

        knowledge_service.sync_with_drive()

        # Should NOT delete drive_id_1 because it's still on Drive
        mock_genai_client.files.delete.assert_not_called()

        # Should upload drive_id_2
        mock_genai_client.file_search_stores.upload_to_file_search_store.assert_called_once()
        kwargs = mock_genai_client.file_search_stores.upload_to_file_search_store.call_args.kwargs
        assert kwargs["file_search_store_name"] == "stores/test-store"
        assert kwargs["config"]["display_name"] == "new.txt [drive_id_2]"


def test_sync_with_drive_delete_removed(
    knowledge_service, mock_settings, mock_genai_client, mock_drive_service
):
    """Test sync deletes files from Gemini that are no longer on Drive."""
    with patch(
        "app.services.knowledge.KnowledgeService._list_drive_files"
    ) as mock_list:
        # Drive is empty, but Gemini has drive_id_1
        mock_list.return_value = []

        knowledge_service.sync_with_drive()

        # Should delete file1 (which maps to drive_id_1)
        mock_genai_client.files.delete.assert_called_once_with(name="files/file1")
        mock_genai_client.file_search_stores.upload_to_file_search_store.assert_not_called()


def test_sync_with_drive_update_modified(
    knowledge_service, mock_settings, mock_genai_client, mock_drive_service
):
    """Test sync updates files if Drive modifiedTime is newer."""
    with (
        patch("app.services.knowledge.KnowledgeService._list_drive_files") as mock_list,
        patch(
            "app.services.knowledge.KnowledgeService._download_single_file"
        ) as mock_download,
    ):
        mock_list.return_value = [
            {
                "id": "drive_id_1",
                "name": "test.txt",
                "mimeType": "text/plain",
                "modifiedTime": "2024-01-02T10:00:00Z",
            },  # newer than Gemini's 2024-01-01
        ]
        mock_download.return_value = (b"content", "test.txt")

        knowledge_service.sync_with_drive()

        # Should delete the old one
        mock_genai_client.files.delete.assert_called_once_with(name="files/file1")

        # Should upload the new one
        mock_genai_client.file_search_stores.upload_to_file_search_store.assert_called_once()
