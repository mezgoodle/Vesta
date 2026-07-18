import asyncio
import hashlib
import io
import logging
import os
import re
import tempfile
from typing import Any

import chromadb
import google.auth
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google import genai
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pymupdf4llm

from app.core.config import settings

logger = logging.getLogger(__name__)

_CHROMA_COLLECTION_NAME = "vesta_knowledge"
_EMBEDDING_MODEL = "gemini-embedding-001"


class KnowledgeService:
    """Service for managing the local RAG knowledge base using direct API calls."""

    def _build_drive_service(self) -> Any:
        """Build Google Drive API service using ADC or service account key."""
        if settings.GOOGLE_APPLICATION_CREDENTIALS and os.path.isfile(
            settings.GOOGLE_APPLICATION_CREDENTIALS
        ):
            creds = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_APPLICATION_CREDENTIALS,
                scopes=["https://www.googleapis.com/auth/drive.readonly"],
            )
        else:
            creds, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/drive.readonly"]
            )
            if not creds.valid:
                creds.refresh(Request())
        return build("drive", "v3", credentials=creds)

    def _list_drive_files(self, service: Any) -> list[dict[str, Any]]:
        """List all files in the configured Drive folder, handling API pagination."""
        query = f"'{settings.GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed = false"
        files = []
        page_token = None
        while True:
            results = (
                service.files()
                .list(
                    q=query,
                    fields="nextPageToken, files(id, name, mimeType)",
                    pageToken=page_token,
                )
                .execute()
            )
            files.extend(results.get("files", []))
            page_token = results.get("nextPageToken")
            if not page_token:
                break
        return files

    def _download_drive_files(
        self,
    ) -> tuple[list[dict[str, Any]], list[tuple[str, str, bytes]]]:
        """Download all files from the configured Drive folder.
        Returns a tuple: (all_drive_files_list, list_of_downloaded_file_tuples).
        """
        service = self._build_drive_service()
        all_files = self._list_drive_files(service)

        downloaded = []
        for file in all_files:
            file_id = file["id"]
            file_name = file["name"]
            mime_type = file["mimeType"]

            # Skip folders
            if mime_type == "application/vnd.google-apps.folder":
                continue

            try:
                # If it's a Google Doc, export it as PDF
                if mime_type.startswith("application/vnd.google-apps."):
                    if "document" in mime_type:
                        export_mime = "application/pdf"
                        file_name = file_name + ".pdf"
                    elif "spreadsheet" in mime_type:
                        export_mime = "application/pdf"
                        file_name = file_name + ".pdf"
                    elif "presentation" in mime_type:
                        export_mime = "application/pdf"
                        file_name = file_name + ".pdf"
                    else:
                        logger.warning(
                            f"Unsupported Google Workspace mime type: {mime_type}"
                        )
                        continue

                    request = service.files().export_media(
                        fileId=file_id, mimeType=export_mime
                    )
                else:
                    request = service.files().get_media(fileId=file_id)

                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()

                downloaded.append((file_id, file_name, fh.getvalue()))
                logger.info(f"Downloaded {file_name} ({file_id}) from Google Drive")
            except Exception as e:
                logger.error(
                    f"Failed to download file {file_name} ({file_id}): {e}",
                    exc_info=True,
                )

        return all_files, downloaded

    def _parse_file(self, file_name: str, file_bytes: bytes) -> str:
        """Parse file content to Markdown string.
        Uses pymupdf4llm for PDFs, and plain text decoding for txt/md.
        """
        try:
            if file_name.lower().endswith(".pdf"):
                with tempfile.NamedTemporaryFile(
                    suffix=".pdf", delete=False
                ) as temp_pdf:
                    temp_pdf.write(file_bytes)
                    temp_pdf_path = temp_pdf.name
                try:
                    md_text = pymupdf4llm.to_markdown(temp_pdf_path)
                    return md_text or ""
                finally:
                    try:
                        os.unlink(temp_pdf_path)
                    except Exception:
                        pass
            else:
                return file_bytes.decode("utf-8", errors="replace")
        except Exception as e:
            logger.error(f"Error parsing file {file_name}: {e}", exc_info=True)
            return ""

    def _chunk_markdown(
        self, text: str, file_id: str, file_name: str
    ) -> list[dict[str, Any]]:
        """Split markdown text by headers.
        If a section is larger than RAG_CHUNK_SIZE, sub-split it with overlap.
        """
        # Split by headers (e.g., #, ##, ###)
        header_pattern = r"(^#+ .+)"
        parts = re.split(header_pattern, text, flags=re.MULTILINE)

        raw_sections = []
        if parts:
            first_part = parts[0].strip()
            if first_part:
                raw_sections.append(("Intro", first_part))

            for i in range(1, len(parts), 2):
                header = parts[i].strip()
                content = parts[i + 1].strip() if i + 1 < len(parts) else ""
                raw_sections.append((header, content))

        chunks = []
        chunk_idx = 0
        chunk_size = settings.RAG_CHUNK_SIZE
        chunk_overlap = settings.RAG_CHUNK_OVERLAP

        for header, content in raw_sections:
            combined_text = f"{header}\n\n{content}".strip()
            if len(combined_text) <= chunk_size:
                chunk_id = hashlib.sha256(f"{file_id}_{chunk_idx}".encode()).hexdigest()
                chunks.append(
                    {
                        "id": chunk_id,
                        "text": combined_text,
                        "metadata": {
                            "file_id": file_id,
                            "file_name": file_name,
                            "header": header,
                        },
                    }
                )
                chunk_idx += 1
            else:
                # Sub-split the content with overlap, accounting for header prefix length
                start = 0
                while start < len(content):
                    prefix = f"{header} (cont.)\n\n"
                    # If prefix is too long, truncate it to guarantee capacity
                    if len(prefix) > chunk_size // 2:
                        truncated_header = header[: chunk_size // 2 - 15] + "..."
                        prefix = f"{truncated_header} (cont.)\n\n"

                    content_capacity = chunk_size - len(prefix)
                    step = content_capacity - chunk_overlap

                    # Ensure loop moves forward
                    if step <= 0:
                        step = max(1, content_capacity // 2)

                    end = start + content_capacity
                    sub_content = content[start:end]
                    sub_text = f"{prefix}{sub_content}".strip()

                    chunk_id = hashlib.sha256(
                        f"{file_id}_{chunk_idx}".encode()
                    ).hexdigest()
                    chunks.append(
                        {
                            "id": chunk_id,
                            "text": sub_text,
                            "metadata": {
                                "file_id": file_id,
                                "file_name": file_name,
                                "header": header,
                            },
                        }
                    )
                    chunk_idx += 1

                    start += step
                    if end >= len(content):
                        break

        return chunks

    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts using Gemini embedding model."""
        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        embeddings = []
        for text in texts:
            response = client.models.embed_content(
                model=_EMBEDDING_MODEL,
                contents=text,
            )
            embeddings.append(response.embeddings[0].values)
        return embeddings

    async def _aembed_query(self, text: str) -> list[float]:
        """Async embed a single query text."""
        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        response = await client.aio.models.embed_content(
            model=_EMBEDDING_MODEL,
            contents=text,
        )
        return response.embeddings[0].values

    def _get_configured_collection(self, chroma_client: Any) -> Any:
        """Get or create collection with cosine similarity space configuration."""
        collection = chroma_client.get_or_create_collection(
            _CHROMA_COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )
        # Migrate existing collection if space config is not cosine
        metadata = collection.metadata or {}
        if metadata.get("hnsw:space") != "cosine":
            logger.warning(
                "ChromaDB collection distance metric mismatch. Recreating with cosine metric."
            )
            try:
                chroma_client.delete_collection(_CHROMA_COLLECTION_NAME)
            except Exception:
                pass
            collection = chroma_client.get_or_create_collection(
                _CHROMA_COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
            )
        return collection

    def sync_with_drive(self) -> None:
        """Sync files from Drive, chunk, embed, and store in ChromaDB."""
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

        all_files, files = self._download_drive_files()
        chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)

        # Clear collection if the Drive inventory is empty
        drive_file_ids = {
            f["id"]
            for f in all_files
            if f["mimeType"] != "application/vnd.google-apps.folder"
        }
        if not drive_file_ids:
            logger.warning(
                "No documents found in Drive folder – clearing index.",
                extra={
                    "json_fields": {
                        "event": "knowledge_sync_empty",
                        "folder_id": settings.GOOGLE_DRIVE_FOLDER_ID,
                    }
                },
            )
            try:
                chroma_client.delete_collection(_CHROMA_COLLECTION_NAME)
            except Exception:
                pass
            self._get_configured_collection(chroma_client)
            return

        all_chunks = []
        downloaded_file_ids = set()
        for file_id, file_name, file_bytes in files:
            downloaded_file_ids.add(file_id)
            markdown_content = self._parse_file(file_name, file_bytes)
            if not markdown_content.strip():
                continue
            chunks = self._chunk_markdown(markdown_content, file_id, file_name)
            all_chunks.extend(chunks)

        if not all_chunks:
            logger.warning("No text chunks generated from downloaded files.")
            return

        logger.info(
            f"Drive documents loaded and chunked: {len(files)} files, "
            f"{len(all_chunks)} chunks total.",
            extra={
                "json_fields": {
                    "event": "knowledge_docs_loaded",
                    "files_count": len(files),
                    "chunks_count": len(all_chunks),
                }
            },
        )

        chunk_texts = [c["text"] for c in all_chunks]
        chunk_embeddings = self._embed_texts(chunk_texts)

        collection = self._get_configured_collection(chroma_client)

        chunk_ids = [c["id"] for c in all_chunks]
        chunk_metadatas = [c["metadata"] for c in all_chunks]

        # Delete prior chunks of the files we are updating to avoid stale chunks
        for file_id in downloaded_file_ids:
            collection.delete(where={"file_id": file_id})

        # Direct upsert into ChromaDB
        collection.upsert(
            ids=chunk_ids,
            embeddings=chunk_embeddings,
            metadatas=chunk_metadatas,
            documents=chunk_texts,
        )

        # Cleanup fully removed files
        existing = collection.get(include=["metadatas"])
        if existing and existing["ids"]:
            to_delete = []
            for idx, meta in enumerate(existing["metadatas"]):
                if meta and "file_id" in meta:
                    file_id = meta["file_id"]
                    if file_id not in drive_file_ids:
                        to_delete.append(existing["ids"][idx])
            if to_delete:
                logger.info(f"Removing deleted documents from index: {to_delete}")
                collection.delete(ids=to_delete)

        logger.info(
            "Drive sync complete – ChromaDB updated.",
            extra={"json_fields": {"event": "knowledge_sync_done"}},
        )

    async def query(self, text: str) -> str:
        """Query ChromaDB and synthesize an answer using Gemini."""
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not set.")
        if not settings.GOOGLE_MODEL_NAME:
            raise ValueError("GOOGLE_MODEL_NAME is not set.")

        try:
            query_embedding = await self._aembed_query(text)

            def _run_chroma_query() -> dict[str, Any]:
                chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
                collection = self._get_configured_collection(chroma_client)
                return collection.query(
                    query_embeddings=[query_embedding],
                    n_results=settings.RAG_SIMILARITY_TOP_K,
                    include=["documents", "metadatas", "distances"],
                )

            results = await asyncio.to_thread(_run_chroma_query)

            relevant_docs = []
            distances = results.get("distances", [[]])[0]
            documents = results.get("documents", [[]])[0]

            passed_cutoff_count = 0
            for idx, doc in enumerate(documents):
                distance = distances[idx]
                similarity = 1.0 - distance
                if similarity >= settings.RAG_SIMILARITY_CUTOFF:
                    relevant_docs.append(doc)
                    passed_cutoff_count += 1

            logger.debug(
                "RAG retrieval",
                extra={
                    "json_fields": {
                        "event": "rag_retrieval",
                        "query": text,
                        "top_k": settings.RAG_SIMILARITY_TOP_K,
                        "cutoff": settings.RAG_SIMILARITY_CUTOFF,
                        "retrieved_count": len(documents),
                        "passed_cutoff": passed_cutoff_count,
                    }
                },
            )

            if not relevant_docs:
                return (
                    "I couldn't find any relevant information in your "
                    "documents to answer this question."
                )

            context = "\n---\n".join(relevant_docs)
            prompt = (
                "You are Vesta, a helpful assistant. Answer the user's question "
                "using only the provided document snippets from their personal knowledge base.\n\n"
                "Guidelines:\n"
                "1. Base your answer strictly on the provided snippets.\n"
                "2. If the snippets do not contain enough information to answer the question, "
                "state that clearly.\n"
                "3. Be concise and precise.\n\n"
                f"Document Snippets:\n{context}\n\n"
                f"User Question: {text}\n"
            )

            client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            response = await client.aio.models.generate_content(
                model=settings.GOOGLE_MODEL_NAME,
                contents=prompt,
            )
            return response.text or ""

        except Exception as e:
            logger.error(
                "Knowledge base query failed",
                extra={
                    "json_fields": {
                        "event": "knowledge_query_error",
                        "error": str(e),
                    }
                },
            )
            raise


knowledge_service_instance = KnowledgeService()


def knowledge_service() -> KnowledgeService:
    return knowledge_service_instance
