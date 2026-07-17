import logging
import os
from typing import Any

import chromadb
from google import genai
from llama_cloud_services import LlamaParse
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.postprocessor import SimilarityPostprocessor
import google.auth
from google.auth.transport.requests import Request
from llama_index.llms.gemini import Gemini
from llama_index.readers.google import GoogleDriveReader as LlamaGoogleDriveReader
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


class GoogleDriveReader(LlamaGoogleDriveReader):
    """
    Subclass of LlamaIndex GoogleDriveReader that supports fallback to
    Application Default Credentials (ADC) when no explicit key/config is provided.
    """
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        service_account_key_path = kwargs.get("service_account_key_path", "service_account_key.json")
        credentials_path = kwargs.get("credentials_path", "credentials.json")
        token_path = kwargs.get("token_path", "token.json")

        has_creds = (
            kwargs.get("client_config") is not None
            or kwargs.get("service_account_key") is not None
            or kwargs.get("authorized_user_info") is not None
            or (service_account_key_path and os.path.isfile(service_account_key_path))
            or (credentials_path and os.path.isfile(credentials_path))
            or (token_path and os.path.isfile(token_path))
        )
        if not has_creds:
            kwargs["client_config"] = {"dummy": "config"}

        super().__init__(*args, **kwargs)

    def _get_credentials(self) -> Any:
        if self.client_config == {"dummy": "config"}:
            from llama_index.readers.google.drive.base import SCOPES
            creds, _ = google.auth.default(scopes=SCOPES)
            if not creds.valid:
                creds.refresh(Request())
            return creds
        
        return super()._get_credentials()


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
        embed_model = self._get_embed_model()

        docstore_json_path = os.path.join(settings.CHROMA_DB_PATH, "docstore.json")
        if os.path.exists(docstore_json_path):
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store,
                persist_dir=settings.CHROMA_DB_PATH,
            )
        else:
            storage_context = StorageContext.from_defaults(vector_store=vector_store)

        index = VectorStoreIndex.from_vector_store(
            vector_store,
            storage_context=storage_context,
            embed_model=embed_model,
        )

        index.refresh_ref_docs(
            documents,
            update_kwargs={"delete_kwargs": {"delete_from_docstore": True}},
        )

        # Remove documents that were deleted from Google Drive
        current_doc_ids = {doc.doc_id for doc in documents}
        ref_doc_infos = storage_context.docstore.get_all_ref_doc_info()
        if ref_doc_infos:
            for ref_doc_id in list(ref_doc_infos.keys()):
                if ref_doc_id not in current_doc_ids:
                    logger.info(
                        f"Removing deleted document from index: {ref_doc_id}"
                    )
                    index.delete_ref_doc(ref_doc_id, delete_from_docstore=True)

        storage_context.persist(persist_dir=settings.CHROMA_DB_PATH)

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
            The query engine's response as a string.

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

            retriever = index.as_retriever(
                similarity_top_k=settings.RAG_SIMILARITY_TOP_K,
            )
            postprocessor = SimilarityPostprocessor(
                similarity_cutoff=settings.RAG_SIMILARITY_CUTOFF,
            )

            query_engine = index.as_query_engine(
                similarity_top_k=settings.RAG_SIMILARITY_TOP_K,
                node_postprocessors=[postprocessor],
                llm=llm,
            )

            raw_nodes = retriever.retrieve(text)
            logger.debug(
                "RAG retrieval",
                extra={
                    "json_fields": {
                        "event": "rag_retrieval",
                        "query": text,
                        "top_k": settings.RAG_SIMILARITY_TOP_K,
                        "cutoff": settings.RAG_SIMILARITY_CUTOFF,
                        "retrieved_count": len(raw_nodes),
                        "passed_cutoff": sum(
                            1
                            for n in raw_nodes
                            if n.score is not None
                            and n.score >= settings.RAG_SIMILARITY_CUTOFF
                        ),
                    }
                },
            )

            response = query_engine.query(text)

            return str(response)
        except Exception as e:
            logger.error(
                "Knowledge base query failed",
                extra={
                    "json_fields": {"event": "knowledge_query_error", "error": str(e)}
                },
            )
            raise


knowledge_service_instance = KnowledgeService()


def knowledge_service() -> KnowledgeService:
    return knowledge_service_instance
