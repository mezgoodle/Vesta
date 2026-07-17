from unittest.mock import ANY, MagicMock, patch

import pytest

from app.services.knowledge import KnowledgeService

# ------------------------------------------------------------------ #
# Shared fixtures                                                       #
# ------------------------------------------------------------------ #


@pytest.fixture
def mock_settings():
    with patch("app.services.knowledge.settings") as m:
        m.LLAMA_PARSE_API_KEY = "test-llama-key"
        m.GOOGLE_DRIVE_FOLDER_ID = "test-folder-id"
        m.GOOGLE_API_KEY = "test-google-key"
        m.GOOGLE_MODEL_NAME = "test-google-model"
        m.CHROMA_DB_PATH = "/tmp/test_chroma"
        m.RAG_SIMILARITY_TOP_K = 5
        m.RAG_SIMILARITY_CUTOFF = 0.55
        yield m


@pytest.fixture
def mock_chroma_client():
    """Patch chromadb.PersistentClient so no filesystem activity occurs."""
    with patch("app.services.knowledge.chromadb.PersistentClient") as mock_cls:
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_cls.return_value = mock_client
        yield mock_cls, mock_collection


# ------------------------------------------------------------------ #
# sync_with_drive                                                       #
# ------------------------------------------------------------------ #


def test_sync_with_drive_success(mock_settings, mock_chroma_client):
    """Full happy-path: documents are loaded, embedded, and the index is built."""
    _, mock_collection = mock_chroma_client

    mock_doc = MagicMock()
    mock_doc.doc_id = "test-doc-id"

    with (
        patch("app.services.knowledge.LlamaParse") as MockParser,
        patch("app.services.knowledge.GoogleDriveReader") as MockReader,
        patch("app.services.knowledge.GoogleGenaiEmbedding"),
        patch("app.services.knowledge.ChromaVectorStore"),
        patch("app.services.knowledge.StorageContext") as MockStorageContext,
        patch("app.services.knowledge.VectorStoreIndex") as MockIndex,
        patch("app.services.knowledge.os.path.exists", return_value=False),
    ):
        MockReader.return_value.load_data.return_value = [mock_doc]

        mock_storage_ctx = MagicMock()
        mock_storage_ctx.docstore.get_all_ref_doc_info.return_value = {}
        MockStorageContext.from_defaults.return_value = mock_storage_ctx

        mock_index_instance = MagicMock()
        MockIndex.from_vector_store.return_value = mock_index_instance

        svc = KnowledgeService()
        svc.sync_with_drive()

        # Reader must be called with the correct folder
        MockReader.assert_called_once()
        MockReader.return_value.load_data.assert_called_once_with(
            folder_id="test-folder-id"
        )

        # Index must be initialized from vector store
        MockIndex.from_vector_store.assert_called_once()

        # refresh_ref_docs must be called with the documents
        mock_index_instance.refresh_ref_docs.assert_called_once_with(
            [mock_doc],
        )

        # Storage context must be persisted
        mock_storage_ctx.persist.assert_called_once_with(persist_dir="/tmp/test_chroma")

        # LlamaParse must be configured as a file extractor
        MockParser.assert_called_once_with(
            api_key="test-llama-key", result_type="markdown"
        )


def test_sync_with_drive_incremental_existing_and_deleted(mock_settings, mock_chroma_client):
    """Happy-path when docstore exists, loading existing context and cleaning up deleted docs."""
    _, mock_collection = mock_chroma_client

    mock_doc = MagicMock()
    mock_doc.doc_id = "new-doc-id"

    with (
        patch("app.services.knowledge.LlamaParse"),
        patch("app.services.knowledge.GoogleDriveReader") as MockReader,
        patch("app.services.knowledge.GoogleGenaiEmbedding"),
        patch("app.services.knowledge.ChromaVectorStore"),
        patch("app.services.knowledge.StorageContext") as MockStorageContext,
        patch("app.services.knowledge.VectorStoreIndex") as MockIndex,
        patch("app.services.knowledge.os.path.exists", return_value=True),
    ):
        MockReader.return_value.load_data.return_value = [mock_doc]

        mock_storage_ctx = MagicMock()
        # Simulated existing docstore containing 'old-doc-id'
        mock_storage_ctx.docstore.get_all_ref_doc_info.return_value = {
            "old-doc-id": MagicMock()
        }
        MockStorageContext.from_defaults.return_value = mock_storage_ctx

        mock_index_instance = MagicMock()
        MockIndex.from_vector_store.return_value = mock_index_instance

        svc = KnowledgeService()
        svc.sync_with_drive()

        # Check StorageContext was initialized with persist_dir
        MockStorageContext.from_defaults.assert_called_once_with(
            vector_store=ANY,
            persist_dir="/tmp/test_chroma"
        )

        # Check from_vector_store was called
        MockIndex.from_vector_store.assert_called_once()

        # Check refresh_ref_docs was called with new docs
        mock_index_instance.refresh_ref_docs.assert_called_once_with(
            [mock_doc],
        )

        # Check that 'old-doc-id' was deleted because it is no longer in current_doc_ids
        mock_index_instance.delete_ref_doc.assert_called_once_with(
            "old-doc-id", delete_from_docstore=True
        )

        # Check persist was called
        mock_storage_ctx.persist.assert_called_once_with(persist_dir="/tmp/test_chroma")


def test_sync_with_drive_no_documents(mock_settings, mock_chroma_client):
    """When Google Drive returns no docs, the index is NOT rebuilt."""
    with (
        patch("app.services.knowledge.LlamaParse"),
        patch("app.services.knowledge.GoogleDriveReader") as MockReader,
        patch("app.services.knowledge.GoogleGenaiEmbedding"),
        patch("app.services.knowledge.VectorStoreIndex") as MockIndex,
    ):
        MockReader.return_value.load_data.return_value = []

        svc = KnowledgeService()
        svc.sync_with_drive()

        MockIndex.from_vector_store.assert_not_called()


def test_sync_with_drive_missing_llama_key(mock_chroma_client):
    """Missing LLAMA_PARSE_API_KEY raises ValueError immediately."""
    with patch("app.services.knowledge.settings") as m:
        m.LLAMA_PARSE_API_KEY = ""
        m.GOOGLE_DRIVE_FOLDER_ID = "some-folder"
        svc = KnowledgeService()
        with pytest.raises(ValueError, match="LLAMA_PARSE_API_KEY"):
            svc.sync_with_drive()


def test_sync_with_drive_missing_folder_id(mock_chroma_client):
    """Missing GOOGLE_DRIVE_FOLDER_ID raises ValueError immediately."""
    with patch("app.services.knowledge.settings") as m:
        m.LLAMA_PARSE_API_KEY = "some-key"
        m.GOOGLE_DRIVE_FOLDER_ID = ""
        svc = KnowledgeService()
        with pytest.raises(ValueError, match="GOOGLE_DRIVE_FOLDER_ID"):
            svc.sync_with_drive()


# ------------------------------------------------------------------ #
# query                                                                #
# ------------------------------------------------------------------ #


def test_query_success(mock_settings, mock_chroma_client):
    """query() loads the index from ChromaDB and returns a string response."""
    with (
        patch("app.services.knowledge.GoogleGenaiEmbedding"),
        patch("app.services.knowledge.Gemini"),
        patch("app.services.knowledge.ChromaVectorStore"),
        patch("app.services.knowledge.VectorStoreIndex") as MockIndex,
    ):
        mock_engine = MagicMock()
        mock_response = MagicMock()
        mock_response.__str__ = lambda self: "The answer."
        mock_response.source_nodes = []
        mock_engine.query.return_value = mock_response
        MockIndex.from_vector_store.return_value.as_query_engine.return_value = (
            mock_engine
        )

        result = KnowledgeService().query("What is the recipe for bread?")

        mock_engine.query.assert_called_once_with("What is the recipe for bread?")
        assert result == "The answer."


def test_query_propagates_exception(mock_settings, mock_chroma_client):
    """query() re-raises unexpected exceptions so callers can handle them."""
    with (
        patch("app.services.knowledge.GoogleGenaiEmbedding"),
        patch("app.services.knowledge.Gemini"),
        patch("app.services.knowledge.ChromaVectorStore"),
        patch("app.services.knowledge.VectorStoreIndex") as MockIndex,
    ):
        MockIndex.from_vector_store.side_effect = RuntimeError("DB gone")

        with pytest.raises(RuntimeError, match="DB gone"):
            KnowledgeService().query("anything")


# ------------------------------------------------------------------ #
# LLMService tool integration                                          #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_llm_service_includes_knowledge_tool():
    """consult_knowledge_base must be registered as a Gemini tool."""
    with (
        patch("app.services.llm.genai.Client") as MockClient,
        patch("app.services.llm.settings") as mock_llm_settings,
    ):
        mock_llm_settings.GOOGLE_API_KEY = "key"
        mock_llm_settings.GOOGLE_MODEL_NAME = "gemini-test"
        mock_llm_settings.SYSTEM_INSTRUCTION = "You are Vesta."

        mock_client_instance = MagicMock()
        mock_client_instance.aio.models.generate_content = MagicMock(
            return_value=MagicMock(text="ok", usage_metadata=None)
        )
        MockClient.return_value = mock_client_instance
        mock_client_instance.aio.models.generate_content.__name__ = "generate_content"

        from unittest.mock import AsyncMock

        mock_client_instance.aio.models.generate_content = AsyncMock(
            return_value=MagicMock(text="ok", usage_metadata=None)
        )

        from app.services.llm import LLMService

        svc = LLMService()
        db = AsyncMock()
        await svc.chat("Tell me about my documents.", [], 1, db)

        call_kwargs = mock_client_instance.aio.models.generate_content.call_args.kwargs
        tool_names = [t.__name__ for t in call_kwargs["config"].tools]
        assert "consult_knowledge_base" in tool_names
