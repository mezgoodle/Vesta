import io
import logging
import os
import re
import tempfile
import time
from datetime import UTC, datetime
from typing import Any

import google.auth
from google import genai
from google.auth.transport.requests import Request
from google.genai import types
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from app.core.config import settings

logger = logging.getLogger(__name__)


class KnowledgeService:
    """Service for managing the RAG knowledge base using Gemini File Search API."""

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
        """List all files in the configured Drive folder."""
        query = f"'{settings.GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed = false"
        files = []
        page_token = None
        while True:
            results = (
                service.files()
                .list(
                    q=query,
                    fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
                    pageToken=page_token,
                )
                .execute()
            )
            files.extend(results.get("files", []))
            page_token = results.get("nextPageToken")
            if not page_token:
                break
        return files

    def _download_single_file(
        self, service: Any, file_id: str, file_name: str, mime_type: str
    ) -> tuple[bytes, str] | None:
        """Download a single file's bytes from Google Drive."""
        try:
            # If it's a Google Doc, export it as PDF
            if mime_type.startswith("application/vnd.google-apps."):
                if (
                    "document" in mime_type
                    or "spreadsheet" in mime_type
                    or "presentation" in mime_type
                ):
                    export_mime = "application/pdf"
                    file_name = file_name + ".pdf"
                else:
                    logger.warning(
                        f"Unsupported Google Workspace mime type: {mime_type}"
                    )
                    return None
                request = service.files().export_media(
                    fileId=file_id, mimeType=export_mime
                )
            else:
                request = service.files().get_media(fileId=file_id)

            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk(num_retries=3)

            logger.info(f"Downloaded {file_name} ({file_id}) from Google Drive")
            return fh.getvalue(), file_name
        except Exception as e:
            logger.error(
                f"Failed to download file {file_name} ({file_id}): {e}",
                exc_info=True,
            )
            return None

    def _parse_time(self, time_val: Any) -> datetime:
        """Parse ISO 8601 time string to UTC datetime, or return if already datetime."""
        if isinstance(time_val, datetime):
            return time_val
        if not time_val:
            return datetime.min.replace(tzinfo=UTC)
        time_str = str(time_val).replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(time_str)
        except ValueError:
            return datetime.min.replace(tzinfo=UTC)

    def _get_or_create_store(self, client: genai.Client) -> Any:
        """Get the File Search Store by name, or create it if not found."""
        if hasattr(self, "_store_name") and self._store_name:
            # Create a mock object or just return if we already have it.
            # But wait, we need an object with a .name property.
            class StoreMock:
                name = self._store_name

            return StoreMock()

        store_display_name = getattr(
            settings, "FILE_SEARCH_STORE_DISPLAY_NAME", "vesta-knowledge-base"
        )
        for store in client.file_search_stores.list():
            if store.display_name == store_display_name:
                self._store_name = store.name
                return store

        logger.info(f"Creating new File Search Store: {store_display_name}")
        new_store = client.file_search_stores.create(
            config={"display_name": store_display_name}
        )
        self._store_name = new_store.name
        return new_store

    def sync_with_drive(self) -> None:
        """
        Incrementally sync files from Drive to Gemini File Search Store.
        This is typically called by a background cron job.
        """
        if not settings.GOOGLE_DRIVE_FOLDER_ID:
            logger.error("GOOGLE_DRIVE_FOLDER_ID is not set.")
            return
        if not settings.GOOGLE_API_KEY:
            logger.error("GOOGLE_API_KEY is not set.")
            return

        logger.info(
            "Starting Drive sync",
            extra={
                "json_fields": {
                    "event": "knowledge_sync_start",
                    "folder_id": settings.GOOGLE_DRIVE_FOLDER_ID,
                }
            },
        )

        try:
            drive_service = self._build_drive_service()
            genai_client = genai.Client(api_key=settings.GOOGLE_API_KEY)

            store = self._get_or_create_store(genai_client)

            # Get Drive files
            drive_files = self._list_drive_files(drive_service)
            drive_files_dict = {
                f["id"]: f
                for f in drive_files
                if f["mimeType"] != "application/vnd.google-apps.folder"
            }

            # Get Gemini files
            gemini_files = list(genai_client.files.list())

            # Match Gemini files to Drive files via display_name format "filename [drive_id]"
            pattern = re.compile(r"^(.*) \[(.*)\]$")
            gemini_files_by_drive_id = {}
            for g_file in gemini_files:
                if not g_file.display_name:
                    continue
                match = pattern.match(g_file.display_name)
                if match:
                    drive_id = match.group(2)
                    gemini_files_by_drive_id[drive_id] = g_file

            # 1. Delete files from Gemini that are no longer on Drive
            for drive_id, g_file in gemini_files_by_drive_id.items():
                if drive_id not in drive_files_dict:
                    logger.info(
                        f"Deleting removed file from Gemini: {g_file.display_name}"
                    )
                    genai_client.files.delete(name=g_file.name)

            # 2. Upload new or modified files
            uploaded_count = 0
            for file_id, d_file in drive_files_dict.items():
                file_name = d_file["name"]
                mime_type = d_file["mimeType"]
                d_mod_time = self._parse_time(d_file.get("modifiedTime", ""))

                g_file = gemini_files_by_drive_id.get(file_id)
                needs_upload = False

                if not g_file:
                    needs_upload = True
                else:
                    g_update_time = self._parse_time(getattr(g_file, "update_time", ""))
                    # Add a small buffer since Gemini update time might differ slightly
                    if d_mod_time > g_update_time:
                        logger.info(f"File modified on Drive, updating: {file_name}")
                        genai_client.files.delete(name=g_file.name)
                        needs_upload = True

                if needs_upload:
                    logger.info(f"Downloading {file_name} from Drive...")
                    download_res = self._download_single_file(
                        drive_service, file_id, file_name, mime_type
                    )
                    if not download_res:
                        continue
                    file_bytes, effective_file_name = download_res

                    # Create temp file and upload
                    ext = os.path.splitext(effective_file_name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                        tmp.write(file_bytes)
                        tmp_path = tmp.name

                    try:
                        logger.info(
                            f"Uploading {effective_file_name} to File Search Store..."
                        )
                        display_name = f"{effective_file_name} [{file_id}]"

                        # Upload directly to the store
                        operation = (
                            genai_client.file_search_stores.upload_to_file_search_store(
                                file=tmp_path,
                                file_search_store_name=store.name,
                                config={"display_name": display_name},
                            )
                        )

                        # Poll until complete
                        deadline = time.time() + 300  # 5 minutes
                        while not getattr(operation, "done", True):
                            if time.time() > deadline:
                                raise TimeoutError("Upload operation timed out")
                            time.sleep(3)
                            operation = genai_client.operations.get(operation=operation)

                        if getattr(operation, "error", None):
                            raise Exception(
                                f"Upload operation failed: {operation.error}"
                            )

                        uploaded_count += 1
                        logger.info(
                            f"Successfully processed and indexed {effective_file_name}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to upload {effective_file_name}: {e}",
                            exc_info=True,
                        )
                    finally:
                        try:
                            os.unlink(tmp_path)
                        except OSError:
                            pass

            logger.info(
                f"Drive sync complete. Uploaded/updated {uploaded_count} files.",
                extra={"json_fields": {"event": "knowledge_sync_done"}},
            )

        except Exception as e:
            logger.error(
                "Drive sync failed",
                extra={
                    "json_fields": {"event": "knowledge_sync_error", "error": str(e)}
                },
                exc_info=True,
            )

    async def query(self, text: str) -> str:
        """Query the Gemini File Search API directly for an answer."""
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not set.")
        if not settings.GOOGLE_MODEL_NAME:
            raise ValueError("GOOGLE_MODEL_NAME is not set.")

        try:
            client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            store = self._get_or_create_store(client)

            logger.debug(
                "RAG retrieval via Gemini File Search",
                extra={
                    "json_fields": {
                        "event": "rag_retrieval",
                        "query": text,
                        "store_name": store.name,
                    }
                },
            )

            prompt = (
                "You are Vesta, a helpful assistant. Answer the user's question "
                "using the attached knowledge base files. \n\n"
                "Guidelines:\n"
                "1. Base your answer strictly on the provided documents.\n"
                "2. If the documents do not contain enough information, state that clearly.\n"
                "3. Be concise and precise.\n\n"
                f"User Question: {text}\n"
            )

            response = await client.aio.models.generate_content(
                model=settings.GOOGLE_MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[
                        types.Tool(
                            file_search=types.FileSearch(
                                file_search_store_names=[store.name]
                            )
                        )
                    ]
                ),
            )

            return response.text or "I couldn't find any relevant information."

        except Exception as e:
            logger.error(
                "Knowledge base query failed",
                extra={
                    "json_fields": {
                        "event": "knowledge_query_error",
                        "error": str(e),
                    }
                },
                exc_info=True,
            )
            return "I couldn't search the knowledge base right now."


knowledge_service_instance = KnowledgeService()


def knowledge_service() -> KnowledgeService:
    return knowledge_service_instance
