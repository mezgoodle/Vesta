import asyncio
import io
import logging
import os
from datetime import datetime, timezone
from typing import Any

import google.auth
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from app.core.config import settings

logger = logging.getLogger(__name__)


class MemoryArchiverService:
    """Service for archiving deleted chat sessions to Google Drive for RAG indexing."""

    def _build_drive_service(self) -> Any:
        """
        Build Google Drive API service with write access (drive.file scope)
        using Service Account key or Application Default Credentials.
        """
        scopes = ["https://www.googleapis.com/auth/drive.file"]

        if settings.GOOGLE_APPLICATION_CREDENTIALS and os.path.isfile(
            settings.GOOGLE_APPLICATION_CREDENTIALS
        ):
            creds = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_APPLICATION_CREDENTIALS,
                scopes=scopes,
            )
        else:
            creds, _ = google.auth.default(scopes=scopes)
            if not creds.valid:
                creds.refresh(Request())

        return build("drive", "v3", credentials=creds)

    def format_session_to_markdown(
        self, session_data: dict[str, Any], messages_data: list[dict[str, Any]]
    ) -> str:
        """
        Format session and message snapshots into structured Markdown optimized for RAG.

        Args:
            session_data: Dict with keys 'id', 'user_id', 'title', 'summary', 'created_at'.
            messages_data: List of dicts with keys 'role', 'content', 'created_at'.

        Returns:
            Formatted Markdown string.
        """
        session_id = session_data.get("id", "Unknown")
        user_id = session_data.get("user_id", "Unknown")
        title = session_data.get("title", "Untitled Session")
        summary = session_data.get("summary") or "No summary available."
        created_at = session_data.get("created_at") or "Unknown"
        archived_at = datetime.now(timezone.utc).isoformat()

        md_parts = [
            f"# Chat Session: {title}\n",
            "## Metadata",
            f"- **Session ID:** {session_id}",
            f"- **User ID:** {user_id}",
            f"- **Created:** {created_at}",
            f"- **Archived:** {archived_at}",
            f"- **Message Count:** {len(messages_data)}\n",
            "## Summary",
            f"{summary}\n",
            "---",
            "\n## Conversation\n",
        ]

        for msg in messages_data:
            role = msg.get("role", "unknown")
            content = msg.get("content", "").strip()
            md_parts.append(f"**{role}:** {content}\n")

        return "\n".join(md_parts)

    def _upload_to_drive_sync(self, filename: str, content: str) -> str | None:
        """
        Synchronous helper to upload Markdown content to Google Drive.

        Args:
            filename: Target file name (e.g. 'user_1_session_10.md').
            content: Markdown content string.

        Returns:
            Google Drive File ID if successful, None otherwise.
        """
        if not settings.GOOGLE_DRIVE_FOLDER_ID:
            logger.error("GOOGLE_DRIVE_FOLDER_ID is not configured. Cannot archive session.")
            return None

        try:
            drive_service = self._build_drive_service()
            file_metadata = {
                "name": filename,
                "parents": [settings.GOOGLE_DRIVE_FOLDER_ID],
                "mimeType": "text/markdown",
            }

            media = MediaIoBaseUpload(
                io.BytesIO(content.encode("utf-8")),
                mimetype="text/markdown",
                resumable=True,
            )

            uploaded_file = (
                drive_service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )

            file_id = uploaded_file.get("id")
            logger.info(
                f"Successfully archived session file '{filename}' to Drive (ID: {file_id})",
                extra={
                    "json_fields": {
                        "event": "session_archive_success",
                        "filename": filename,
                        "file_id": file_id,
                    }
                },
            )
            return file_id

        except Exception as e:
            logger.error(
                f"Failed to upload archived session '{filename}' to Google Drive: {e}",
                extra={
                    "json_fields": {
                        "event": "session_archive_error",
                        "filename": filename,
                        "error": str(e),
                    }
                },
                exc_info=True,
            )
            return None

    async def upload_to_drive(self, filename: str, content: str) -> str | None:
        """
        Asynchronously upload Markdown content to Google Drive via thread pool.

        Args:
            filename: Target file name on Google Drive.
            content: Raw Markdown content.

        Returns:
            File ID if successful, None otherwise.
        """
        return await asyncio.to_thread(self._upload_to_drive_sync, filename, content)

    async def archive_session(
        self, session_data: dict[str, Any], messages_data: list[dict[str, Any]]
    ) -> None:
        """
        Background task entry point: format session to Markdown and upload to Drive.

        Args:
            session_data: Snapshot of session data.
            messages_data: Snapshot of messages list.
        """
        if not settings.SESSION_ARCHIVE_ENABLED:
            logger.info("Session archival is disabled via settings.")
            return

        if not messages_data:
            logger.info(
                f"Skipping archival for session {session_data.get('id')} — no messages to archive."
            )
            return

        user_id = session_data.get("user_id", "0")
        session_id = session_data.get("id", "0")
        filename = f"user_{user_id}_session_{session_id}.md"

        logger.info(
            f"Starting background archival for session {session_id} (user {user_id})..."
        )
        content = self.format_session_to_markdown(session_data, messages_data)
        await self.upload_to_drive(filename, content)


archiver_service_instance = MemoryArchiverService()


def archiver_service() -> MemoryArchiverService:
    return archiver_service_instance
