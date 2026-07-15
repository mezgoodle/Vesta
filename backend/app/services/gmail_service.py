import asyncio
import base64
import json
import logging
from typing import Any

from bs4 import BeautifulSoup
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.crud_user import user as crud_user
from app.schemas.gmail import EmailMessage

logger = logging.getLogger(__name__)


class GmailService:
    """Service for interacting with Google Gmail API."""

    def __init__(self) -> None:
        """Initialize the Gmail Service."""
        self.token_uri = "https://oauth2.googleapis.com/token"

    async def _get_gmail_client(self, user_id: int, db: AsyncSession) -> Any:
        """
        Build and return an authenticated Google Gmail API service.

        Args:
            user_id: The ID of the user
            db: Database session

        Returns:
            Authenticated Google Gmail service resource

        Raises:
            ValueError: If user not found, not authenticated, or service creation fails
        """
        user = await crud_user.get(db, id=user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        if not user.google_refresh_token:
            raise ValueError(
                f"User {user_id} has not authorized Google access. "
                "Please complete OAuth flow first."
            )

        try:
            credentials = Credentials(
                token=None,
                refresh_token=user.google_refresh_token,
                token_uri=self.token_uri,
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET.get_secret_value(),
            )
        except Exception as e:
            raise ValueError(f"Failed to create credentials: {str(e)}") from e

        try:
            return await asyncio.to_thread(
                build, "gmail", "v1", credentials=credentials
            )
        except Exception as e:
            raise ValueError(f"Failed to build Gmail service: {str(e)}") from e

    def _extract_body_parts(self, payload: dict[str, Any]) -> tuple[str | None, str | None]:
        """
        Recursively extract plain text and HTML parts from the message payload.

        Returns:
            A tuple of (text_plain, text_html).
        """
        mime_type = payload.get("mimeType")
        body = payload.get("body", {})
        data = body.get("data")

        text_plain = None
        text_html = None

        if data:
            try:
                # Gmail base64url encodes the body parts
                decoded = base64.urlsafe_b64decode(data.encode("utf-8")).decode(
                    "utf-8", errors="ignore"
                )
                if mime_type == "text/plain":
                    text_plain = decoded
                elif mime_type == "text/html":
                    text_html = decoded
            except Exception as e:
                logger.debug("Failed decoding body part: %s", e)

        # Process parts recursively if present
        parts = payload.get("parts", [])
        for part in parts:
            part_plain, part_html = self._extract_body_parts(part)
            if part_plain and not text_plain:
                text_plain = part_plain
            if part_html and not text_html:
                text_html = part_html
            # Early break if we have both
            if text_plain and text_html:
                break

        return text_plain, text_html

    def _extract_body(self, payload: dict[str, Any]) -> str:
        """
        Extract the plain text body from the Gmail message payload.
        Strips HTML using BeautifulSoup if only HTML is available.
        """
        text_plain, text_html = self._extract_body_parts(payload)

        if text_plain:
            return text_plain.strip()

        if text_html:
            try:
                soup = BeautifulSoup(text_html, "html.parser")
                # Decompose script and style blocks
                for element in soup(["script", "style"]):
                    element.decompose()
                text = soup.get_text(separator="\n")
                # Clean up excess whitespace
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                return "\n".join(lines)
            except Exception as e:
                logger.warning("BeautifulSoup parsing failed: %s", e)
                return ""

        return ""

    def _get_messages_sync(
        self, service: Any, query: str, max_results: int
    ) -> list[EmailMessage]:
        """
        Synchronous helper to list and fetch messages from Gmail API.
        """
        try:
            # List messages matching the query
            results = (
                service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results)
                .execute()
            )
            message_summaries = results.get("messages", [])

            emails = []
            for msg_summary in message_summaries:
                msg_id = msg_summary["id"]
                # Fetch full message content
                msg = (
                    service.users()
                    .messages()
                    .get(userId="me", id=msg_id, format="full")
                    .execute()
                )

                payload = msg.get("payload", {})
                headers = payload.get("headers", [])
                snippet = msg.get("snippet", "")

                # Extract metadata headers
                sender = "Unknown Sender"
                subject = "No Subject"
                date = "Unknown Date"

                for header in headers:
                    name = header.get("name", "").lower()
                    if name == "from":
                        sender = header.get("value", sender)
                    elif name == "subject":
                        subject = header.get("value", subject)
                    elif name == "date":
                        date = header.get("value", date)

                # Extract and clean body content
                body = self._extract_body(payload)

                # If no body was found, fall back to snippet
                if not body:
                    body = snippet

                # Truncate long bodies to save LLM context window
                truncate_len = settings.GMAIL_BODY_TRUNCATE_LEN
                if len(body) > truncate_len:
                    body = body[:truncate_len] + "\n... [truncated]"

                emails.append(
                    EmailMessage(
                        id=msg_id,
                        sender=sender,
                        subject=subject,
                        date=date,
                        snippet=snippet,
                        body=body,
                    )
                )

            return emails

        except HttpError as e:
            logger.error("Google Gmail API HttpError: %s", e)
            raise
        except Exception as e:
            logger.error("Failed executing sync Gmail fetch: %s", e)
            raise

    async def get_emails(
        self,
        user_id: int,
        db: AsyncSession,
        query: str = "is:unread",
        max_results: int = 5,
    ) -> list[EmailMessage]:
        """
        Search and retrieve parsed user emails asynchronously.

        Args:
            user_id: User database ID
            db: Database session
            query: Gmail search query (e.g. "is:unread", "from:someone@gmail.com")
            max_results: Max messages to return

        Returns:
            List of EmailMessage models
        """
        service = await self._get_gmail_client(user_id, db)
        try:
            return await asyncio.to_thread(
                self._get_messages_sync, service, query, max_results
            )
        except RefreshError as e:
            await self._handle_auth_error(user_id, db, e)
            raise RefreshError(
                f"Failed to refresh access token for user {user_id}. "
                "Re-authorization required."
            ) from e
        except HttpError as e:
            await self._handle_auth_error(user_id, db, e)
            if e.resp.status == 403:
                try:
                    err_data = json.loads(e.content.decode("utf-8"))
                    error_details = err_data.get("error", {})
                    message = error_details.get("message", "").lower()
                    errors = error_details.get("errors", [])
                    reasons = [err.get("reason", "") for err in errors]
                    is_scope_error = (
                        "scope" in message
                        or "insufficient" in message
                        or any(
                            r in ("ACCESS_TOKEN_SCOPE_INSUFFICIENT", "insufficientPermissions")
                            for r in reasons
                        )
                    )
                    if is_scope_error:
                        raise ValueError(
                            "Gmail access is not authorized. Please run the Google OAuth flow "
                            "again to grant Vesta permission to read your emails."
                        ) from e
                except (json.JSONDecodeError, TypeError, KeyError):
                    pass
            raise
        except Exception:
            raise

    def _get_email_sync(self, service: Any, message_id: str) -> EmailMessage:
        """
        Synchronous helper to fetch a single message by ID.
        """
        try:
            msg = (
                service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
            payload = msg.get("payload", {})
            headers = payload.get("headers", [])
            snippet = msg.get("snippet", "")

            sender = "Unknown Sender"
            subject = "No Subject"
            date = "Unknown Date"

            for header in headers:
                name = header.get("name", "").lower()
                if name == "from":
                    sender = header.get("value", sender)
                elif name == "subject":
                    subject = header.get("value", subject)
                elif name == "date":
                    date = header.get("value", date)

            body = self._extract_body(payload)
            if not body:
                body = snippet

            truncate_len = settings.GMAIL_BODY_TRUNCATE_LEN
            if len(body) > truncate_len:
                body = body[:truncate_len] + "\n... [truncated]"

            return EmailMessage(
                id=message_id,
                sender=sender,
                subject=subject,
                date=date,
                snippet=snippet,
                body=body,
            )
        except HttpError as e:
            logger.error("Google Gmail API HttpError for message %s: %s", message_id, e)
            raise
        except Exception as e:
            logger.error("Failed executing sync Gmail get for message %s: %s", message_id, e)
            raise

    async def get_email_by_id(
        self,
        user_id: int,
        db: AsyncSession,
        message_id: str,
    ) -> EmailMessage:
        """
        Retrieve a single email message by ID asynchronously.
        """
        service = await self._get_gmail_client(user_id, db)
        try:
            return await asyncio.to_thread(
                self._get_email_sync, service, message_id
            )
        except RefreshError as e:
            await self._handle_auth_error(user_id, db, e)
            raise RefreshError(
                f"Failed to refresh access token for user {user_id}. "
                "Re-authorization required."
            ) from e
        except HttpError as e:
            await self._handle_auth_error(user_id, db, e)
            if e.resp.status == 403:
                try:
                    err_data = json.loads(e.content.decode("utf-8"))
                    error_details = err_data.get("error", {})
                    message = error_details.get("message", "").lower()
                    errors = error_details.get("errors", [])
                    reasons = [err.get("reason", "") for err in errors]
                    is_scope_error = (
                        "scope" in message
                        or "insufficient" in message
                        or any(
                            r in ("ACCESS_TOKEN_SCOPE_INSUFFICIENT", "insufficientPermissions")
                            for r in reasons
                        )
                    )
                    if is_scope_error:
                        raise ValueError(
                            "Gmail access is not authorized. Please run the Google OAuth flow "
                            "again to grant Vesta permission to read your emails."
                        ) from e
                except (json.JSONDecodeError, TypeError, KeyError):
                    pass
            raise
        except Exception:
            raise

    async def _handle_auth_error(
        self, user_id: int, db: AsyncSession, exception: Exception
    ) -> None:
        """Update google_token_status when an auth error is encountered."""
        status_val = None
        if isinstance(exception, RefreshError):
            status_val = "expired"
        elif isinstance(exception, HttpError):
            if exception.resp.status == 403:
                try:
                    err_data = json.loads(exception.content.decode("utf-8"))
                    error_details = err_data.get("error", {})
                    message = error_details.get("message", "").lower()
                    errors = error_details.get("errors", [])
                    reasons = [err.get("reason", "") for err in errors]
                    is_scope_error = (
                        "scope" in message
                        or "insufficient" in message
                        or any(
                            r in ("ACCESS_TOKEN_SCOPE_INSUFFICIENT", "insufficientPermissions")
                            for r in reasons
                        )
                    )
                    if is_scope_error:
                        status_val = "revoked"
                except Exception:
                    if any(phrase in str(exception).lower() for phrase in ("scope", "insufficient", "permission")):
                        status_val = "revoked"
            elif exception.resp.status == 401:
                status_val = "expired"

        if status_val:
            try:
                user = await crud_user.get(db, id=user_id)
                if user and user.google_token_status != status_val:
                    await crud_user.update(
                        db, db_obj=user, obj_in={"google_token_status": status_val}
                    )
            except Exception as e:
                await db.rollback()
                logger.error("Failed to update google_token_status for user %s: %s", user_id, e)


gmail_service_instance = GmailService()


def gmail_service() -> GmailService:
    return gmail_service_instance
