import logging
import os
from typing import Any

import chromadb
from google import genai
from llama_cloud_services import LlamaParse
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.llms.gemini import Gemini
from llama_index.readers.google import GoogleDriveReader
from llama_index.vector_stores.chroma import ChromaVectorStore
from pydantic import Field

from app.core.config import settings

logger = logging.getLogger(__name__)

_SA_CREDENTIALS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "logger_sa.json",
)
_CHROMA_COLLECTION_NAME = "vesta_knowledge"
_EMBEDDING_MODEL = "gemini-embedding-001"


# ------------------------------------------------------------------ #
# Custom Gemini Embedder (uses google.genai – no legacy SDK)          #
# ------------------------------------------------------------------ #


class GoogleGenaiEmbedding(BaseEmbedding):
    """
    LlamaIndex-compatible embedder that delegates to the ``google.genai``
    SDK (the same SDK used by the rest of the Vesta backend).

    This avoids taking a dependency on ``llama-index-embeddings-gemini``,
    which still relies on the deprecated ``google-generativeai`` package.
    """

    api_key: str = Field(description="Google API key")
    model: str = Field(
        default=_EMBEDDING_MODEL,
        description="Gemini embedding model name",
    )

    def __init__(
        self,
        api_key: str,
        model: str = _EMBEDDING_MODEL,
        **kwargs: Any,
    ) -> None:
        super().__init__(api_key=api_key, model=model, **kwargs)
        self._client = genai.Client(api_key=api_key)

    # -- sync interface (required by BaseEmbedding) --

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._embed(query)

    def _get_text_embedding(self, text: str) -> list[float]:
        return self._embed(text)

    def _get_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    # -- async interface (optional but avoids thread-pool overhead) --

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return await self._aembed(query)

    async def _aget_text_embedding(self, text: str) -> list[float]:
        return await self._aembed(text)

    # -- helpers --

    def _embed(self, text: str) -> list[float]:
        response = self._client.models.embed_content(
            model=self.model,
            contents=text,
        )
        return response.embeddings[0].values

    async def _aembed(self, text: str) -> list[float]:
        response = await self._client.aio.models.embed_content(
            model=self.model,
            contents=text,
        )
        return response.embeddings[0].values


# ------------------------------------------------------------------ #
# KnowledgeService                                                     #
# ------------------------------------------------------------------ #


class KnowledgeService:
    """Service for managing the local RAG knowledge base."""

    def _get_embed_model(self) -> GoogleGenaiEmbedding:
        return GoogleGenaiEmbedding(
            model="gemini-embedding-001",
            api_key=settings.GOOGLE_API_KEY,
        )

    def _get_chroma_store(self) -> ChromaVectorStore:
        """Return a ChromaVectorStore backed by a PersistentClient."""
        client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
        collection = client.get_or_create_collection(_CHROMA_COLLECTION_NAME)
        return ChromaVectorStore(chroma_collection=collection)

    # ------------------------------------------------------------------ #
    # sync_with_drive                                                      #
    # ------------------------------------------------------------------ #

    def sync_with_drive(self) -> None:
        """
        Pull files from Google Drive, embed them, and persist into ChromaDB.

        Designed to run as a FastAPI BackgroundTask (synchronous, executes in
        the default thread-pool executor so it doesn't block the event loop).

        Raises:
            ValueError: If required settings (LLAMA_PARSE_API_KEY,
                        GOOGLE_DRIVE_FOLDER_ID) are not configured.
        """
        if not settings.LLAMA_PARSE_API_KEY:
            raise ValueError(
                "LLAMA_PARSE_API_KEY is not set. "
                "Get a free key at https://cloud.llamaindex.ai"
            )
        if not settings.GOOGLE_DRIVE_FOLDER_ID:
            raise ValueError("GOOGLE_DRIVE_FOLDER_ID is not set.")

        logger.info(
            "Starting Drive sync",
            extra={
                "json_fields": {
                    "event": "knowledge_sync_start",
                    "folder_id": settings.GOOGLE_DRIVE_FOLDER_ID,
                }
            },
        )

        # --- 1. Parse PDFs with LlamaParse (llama-cloud-services) ---
        parser = LlamaParse(
            api_key=settings.LLAMA_PARSE_API_KEY,
            result_type="markdown",
        )
        file_extractor = {".pdf": parser}

        reader = GoogleDriveReader(
            service_account_key_path=settings.GOOGLE_APPLICATION_CREDENTIALS,
            file_extractor=file_extractor,
        )
        documents = reader.load_data(folder_id=settings.GOOGLE_DRIVE_FOLDER_ID)

        if not documents:
            logger.warning(
                "No documents found in Drive folder – index not updated.",
                extra={
                    "json_fields": {
                        "event": "knowledge_sync_empty",
                        "folder_id": settings.GOOGLE_DRIVE_FOLDER_ID,
                    }
                },
            )
            return

        logger.info(
            "Drive documents loaded",
            extra={
                "json_fields": {
                    "event": "knowledge_docs_loaded",
                    "count": len(documents),
                }
            },
        )

        # --- 3. Embed + store into ChromaDB ---
        vector_store = self._get_chroma_store()
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        embed_model = self._get_embed_model()

        VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            embed_model=embed_model,
            show_progress=True,
        )

        logger.info(
            "Drive sync complete – ChromaDB updated.",
            extra={"json_fields": {"event": "knowledge_sync_done"}},
        )

    # ------------------------------------------------------------------ #
    # query                                                                #
    # ------------------------------------------------------------------ #

    def _get_llm(self) -> Gemini:
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not set.")
        if not settings.GOOGLE_MODEL_NAME:
            raise ValueError("GOOGLE_MODEL_NAME is not set.")

        return Gemini(
            api_key=settings.GOOGLE_API_KEY,
            model_name=settings.GOOGLE_MODEL_NAME,
        )

    def query(self, text: str) -> str:
        """
        Query the local ChromaDB knowledge base and return a plain-text answer.

        The index is loaded from the persisted ChromaDB store on every call,
        so the latest synced data is always used without rebuilding the index.

        Args:
            text: Natural-language query string.

        Returns:
            The query engine's response as a string, or a human-readable
            fallback message if the knowledge base has not been synced yet.

        Raises:
            Exception: Re-raises unexpected errors after logging them.
        """
        try:
            vector_store = self._get_chroma_store()
            embed_model = self._get_embed_model()
            llm = self._get_llm()
            index = VectorStoreIndex.from_vector_store(
                vector_store,
                embed_model=embed_model,
            )
            query_engine = index.as_query_engine(llm=llm)
            response = query_engine.query(text)
            return str(response)
        except Exception:
            logger.error(
                "Knowledge base query failed",
                extra={"json_fields": {"event": "knowledge_query_error"}},
            )
            raise


knowledge_service_instance = KnowledgeService()


def knowledge_service() -> KnowledgeService:
    return knowledge_service_instance
