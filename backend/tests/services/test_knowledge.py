import io
import pytest
from unittest.mock import ANY, AsyncMock, MagicMock, patch

from app.services.knowledge import KnowledgeService


@pytest.fixture
def mock_settings():
    with patch("app.services.knowledge.settings") as m:
        m.GOOGLE_DRIVE_FOLDER_ID = "test-folder-id"
        m.GOOGLE_API_KEY = "test-google-key"
        m.GOOGLE_MODEL_NAME = "test-google-model"
        m.GOOGLE_APPLICATION_CREDENTIALS = ""  # Explicitly empty to avoid reading real credentials
        m.CHROMA_DB_PATH = "/tmp/test_chroma"
        m.RAG_SIMILARITY_TOP_K = 5
        m.RAG_SIMILARITY_CUTOFF = 0.55
        m.RAG_CHUNK_SIZE = 1000
        m.RAG_CHUNK_OVERLAP = 200
        yield m


@pytest.fixture
def mock_chroma_client():
    with patch("app.services.knowledge.chromadb.PersistentClient") as mock_cls:
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_cls.return_value = mock_client
        yield mock_cls, mock_collection


@pytest.fixture
def mock_genai_client():
    with patch("app.services.knowledge.genai.Client") as MockClient:
        mock_instance = MagicMock()
        MockClient.return_value = mock_instance

        # Mock sync embed_content
        mock_emb = MagicMock()
        mock_emb.values = [0.1, 0.2]
        mock_instance.models.embed_content.return_value.embeddings = [mock_emb]

        # Mock async aembed_query as an AsyncMock
        mock_emb_async = MagicMock()
        mock_emb_async.values = [0.1, 0.2]
        mock_res_embed = MagicMock()
        mock_res_embed.embeddings = [mock_emb_async]
        mock_instance.aio.models.embed_content = AsyncMock(return_value=mock_res_embed)

        # Mock async generate_content as an AsyncMock
        mock_res_gen = MagicMock()
        mock_res_gen.text = "Mock synthesized answer"
        mock_instance.aio.models.generate_content = AsyncMock(return_value=mock_res_gen)

        yield mock_instance


@pytest.fixture
def mock_drive_api():
    with (
        patch("app.services.knowledge.build") as mock_build,
        patch("app.services.knowledge.MediaIoBaseDownload") as MockDownload,
        patch("app.services.knowledge.google.auth.default") as mock_adc,
    ):
        mock_adc.return_value = (MagicMock(), "project-id")
        
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_files_list = mock_service.files.return_value.list
        mock_files_list.return_value.execute.return_value = {
            "files": [
                {"id": "file1", "name": "doc1.pdf", "mimeType": "application/pdf"},
                {"id": "file2", "name": "doc2.txt", "mimeType": "text/plain"},
            ]
        }

        # Handle the download file chunk process writing content
        def mock_download_init(fh, request):
            fh.write(b"Mock content for file")
            mock_downloader = MagicMock()
            mock_downloader.next_chunk.return_value = (None, True)
            return mock_downloader

        MockDownload.side_effect = mock_download_init

        yield mock_service


# ------------------------------------------------------------------ #
# sync_with_drive                                                    #
# ------------------------------------------------------------------ #


def test_sync_with_drive_success(
    mock_settings, mock_chroma_client, mock_genai_client, mock_drive_api
):
    """Happy-path: documents are loaded, parsed, chunked, embedded, and saved."""
    _, mock_collection = mock_chroma_client

    with patch(
        "app.services.knowledge.pymupdf4llm.to_markdown",
        return_value="# Header\nThis is a pdf content",
    ) as mock_pdf_parse:
        svc = KnowledgeService()
        svc.sync_with_drive()

        # Check drive API listed files
        mock_drive_api.files.return_value.list.assert_called_once()
        
        # Check pdf parsing was called
        mock_pdf_parse.assert_called_once()

        # Check embeddings were generated
        mock_genai_client.models.embed_content.assert_called()

        # Verify upsert was called with chunks
        mock_collection.upsert.assert_called_once_with(
            ids=ANY,
            embeddings=ANY,
            metadatas=ANY,
            documents=ANY,
        )


def test_sync_with_drive_no_documents(
    mock_settings, mock_chroma_client, mock_genai_client, mock_drive_api
):
    """When Google Drive returns no files, the index is not updated."""
    _, mock_collection = mock_chroma_client

    mock_drive_api.files.return_value.list.return_value.execute.return_value = {
        "files": []
    }

    svc = KnowledgeService()
    svc.sync_with_drive()

    mock_collection.upsert.assert_not_called()


def test_sync_incremental_deletes_removed_files(
    mock_settings, mock_chroma_client, mock_genai_client, mock_drive_api
):
    """Verify that chunks belonging to files no longer in Drive are cleaned up."""
    _, mock_collection = mock_chroma_client

    # Mock ChromaDB returning an existing chunk belonging to "deleted_file"
    mock_collection.get.return_value = {
        "ids": ["old-chunk-id"],
        "metadatas": [{"file_id": "deleted_file", "file_name": "old.txt"}],
    }

    with patch(
        "app.services.knowledge.pymupdf4llm.to_markdown",
        return_value="# Header\nMock content",
    ):
        svc = KnowledgeService()
        svc.sync_with_drive()

        # Verify deleted file chunk was removed
        mock_collection.delete.assert_called_once_with(ids=["old-chunk-id"])


def test_sync_with_drive_missing_folder_id(
    mock_chroma_client, mock_genai_client, mock_drive_api
):
    """Missing GOOGLE_DRIVE_FOLDER_ID raises ValueError immediately."""
    with patch("app.services.knowledge.settings") as m:
        m.GOOGLE_DRIVE_FOLDER_ID = ""
        svc = KnowledgeService()
        with pytest.raises(ValueError, match="GOOGLE_DRIVE_FOLDER_ID"):
            svc.sync_with_drive()


# ------------------------------------------------------------------ #
# query                                                              #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_query_success(
    mock_settings, mock_chroma_client, mock_genai_client
):
    """query() loads chunks, filters by cutoff, and calls Gemini for response."""
    _, mock_collection = mock_chroma_client

    # Mock ChromaDB query results: distance 0.1 -> similarity 0.9 (above 0.55 cutoff)
    mock_collection.query.return_value = {
        "documents": [["Relevant document snippet"]],
        "metadatas": [[{"file_name": "doc1.txt"}]],
        "distances": [[0.1]],
    }

    result = await KnowledgeService().query("What is Vesta?")

    assert result == "Mock synthesized answer"
    mock_collection.query.assert_called_once()
    # Check that generation client was called
    mock_genai_client.aio.models.generate_content.assert_called_once()


@pytest.mark.asyncio
async def test_query_cutoff_filters_results(
    mock_settings, mock_chroma_client, mock_genai_client
):
    """Chunks with similarity below cutoff are filtered out."""
    _, mock_collection = mock_chroma_client

    # Mock ChromaDB query results: distance 0.6 -> similarity 0.4 (below 0.55 cutoff)
    mock_collection.query.return_value = {
        "documents": [["Irrelevant document snippet"]],
        "metadatas": [[{"file_name": "doc1.txt"}]],
        "distances": [[0.6]],
    }

    result = await KnowledgeService().query("What is Vesta?")

    assert "I couldn't find any relevant information" in result
    mock_genai_client.aio.models.generate_content.assert_not_called()


@pytest.mark.asyncio
async def test_query_propagates_exception(
    mock_settings, mock_chroma_client, mock_genai_client
):
    """query() propagates exceptions."""
    _, mock_collection = mock_chroma_client
    mock_collection.query.side_effect = RuntimeError("DB error")

    with pytest.raises(RuntimeError, match="DB error"):
        await KnowledgeService().query("anything")


# ------------------------------------------------------------------ #
# Chunking Unit Tests                                                #
# ------------------------------------------------------------------ #


def test_chunk_markdown_splits_by_headers():
    svc = KnowledgeService()
    text = (
        "# Title\nIntroductory text here.\n"
        "## Section 1\nSome content for section 1.\n"
        "### Subsection 1.1\nContent for subsection."
    )
    chunks = svc._chunk_markdown(text, "file1", "test.md")

    assert len(chunks) == 3
    assert chunks[0]["metadata"]["header"] == "# Title"
    assert chunks[1]["metadata"]["header"] == "## Section 1"
    assert chunks[2]["metadata"]["header"] == "### Subsection 1.1"


def test_chunk_markdown_respects_max_size():
    with patch("app.services.knowledge.settings") as mock_set:
        mock_set.RAG_CHUNK_SIZE = 50
        mock_set.RAG_CHUNK_OVERLAP = 10

        svc = KnowledgeService()
        text = "# Header\n" + "a" * 120
        chunks = svc._chunk_markdown(text, "file1", "test.md")

        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk["text"]) <= 50 + len(" (cont.)")
            assert chunk["text"].startswith("# Header (cont.)") or chunk["text"].startswith("# Header")
