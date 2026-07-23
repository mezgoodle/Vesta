import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.crud_user import user as crud_user
from app.schemas.tasks import TaskItem, TaskList

logger = logging.getLogger(__name__)


def _parse_datetime(dt_str: str | None) -> datetime | None:
    """Safely parse RFC 3339 datetime string from Google API."""
    if not dt_str:
        return None
    try:
        # Standard ISO 8601 / RFC 3339 parsing (replace 'Z' with '+00:00' if needed)
        clean_str = dt_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean_str)
    except Exception:
        return None


def _format_due_datetime(dt: datetime | None) -> str | None:
    """Format Python datetime to RFC 3339 string expected by Google Tasks API."""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


class GoogleTasksService:
    """Service for interacting with Google Tasks API."""

    def __init__(self) -> None:
        """Initialize the Google Tasks Service."""
        self.token_uri = "https://oauth2.googleapis.com/token"

    async def _get_tasks_client(self, user_id: int, db: AsyncSession) -> Any:
        """
        Build and return an authenticated Google Tasks API service.

        Args:
            user_id: The ID of the user
            db: Database session

        Returns:
            Authenticated Google Tasks service resource

        Raises:
            ValueError: If user not found or not authenticated
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
                build, "tasks", "v1", credentials=credentials
            )
        except Exception as e:
            raise ValueError(f"Failed to build Google Tasks service: {str(e)}") from e

    async def get_task_lists(
        self, user_id: int, db: AsyncSession
    ) -> list[TaskList]:
        """
        Get all task lists for the specified user.

        Args:
            user_id: User ID
            db: Database session

        Returns:
            List of TaskList items
        """
        client = await self._get_tasks_client(user_id, db)

        try:
            request = client.tasklists().list()
            response = await asyncio.to_thread(request.execute)
            items = response.get("items", [])
            return [
                TaskList(
                    id=item["id"],
                    title=item.get("title", "Untitled List"),
                    updated=_parse_datetime(item.get("updated")),
                )
                for item in items
            ]
        except RefreshError as e:
            logger.error(
                f"Failed to refresh token for user {user_id}: {e}",
                extra={"json_fields": {"user_id": user_id, "error": str(e)}},
            )
            raise ValueError("Google authorization expired. Please re-authenticate.") from e
        except HttpError as e:
            logger.error(
                f"Google API HTTP error listing task lists for user {user_id}: {e}",
                extra={"json_fields": {"user_id": user_id, "error": str(e)}},
            )
            raise Exception(f"Google API Error: {e.reason}") from e

    async def get_tasks(
        self,
        user_id: int,
        db: AsyncSession,
        tasklist_id: str = "@default",
        show_completed: bool = False,
    ) -> list[TaskItem]:
        """
        Fetch tasks from a Google Task List.

        Args:
            user_id: User ID
            db: Database session
            tasklist_id: ID of the task list (defaults to '@default')
            show_completed: Whether to include completed tasks

        Returns:
            List of TaskItem objects
        """
        client = await self._get_tasks_client(user_id, db)

        try:
            request = client.tasks().list(
                tasklist=tasklist_id,
                showCompleted=show_completed,
                showHidden=show_completed,
            )
            response = await asyncio.to_thread(request.execute)
            items = response.get("items", [])

            tasks: list[TaskItem] = []
            for item in items:
                # Exclude deleted or invalid title tasks if needed
                tasks.append(
                    TaskItem(
                        id=item["id"],
                        title=item.get("title", ""),
                        notes=item.get("notes"),
                        status=item.get("status", "needsAction"),
                        due=_parse_datetime(item.get("due")),
                        completed=_parse_datetime(item.get("completed")),
                        updated=_parse_datetime(item.get("updated")),
                    )
                )
            return tasks
        except RefreshError as e:
            logger.error(
                f"Failed to refresh token for user {user_id}: {e}",
                extra={"json_fields": {"user_id": user_id, "error": str(e)}},
            )
            raise ValueError("Google authorization expired. Please re-authenticate.") from e
        except HttpError as e:
            logger.error(
                f"Google API HTTP error listing tasks for user {user_id}: {e}",
                extra={"json_fields": {"user_id": user_id, "error": str(e)}},
            )
            raise Exception(f"Google API Error: {e.reason}") from e

    async def create_task(
        self,
        user_id: int,
        db: AsyncSession,
        title: str,
        notes: str | None = None,
        due: datetime | None = None,
        tasklist_id: str = "@default",
    ) -> TaskItem:
        """
        Create a new task in Google Tasks.

        Args:
            user_id: User ID
            db: Database session
            title: Title of the task
            notes: Optional notes or description
            due: Optional due date/time
            tasklist_id: Task list ID (defaults to '@default')

        Returns:
            Created TaskItem
        """
        client = await self._get_tasks_client(user_id, db)

        body: dict[str, Any] = {
            "title": title,
        }
        if notes:
            body["notes"] = notes
        if due:
            body["due"] = _format_due_datetime(due)

        try:
            request = client.tasks().insert(tasklist=tasklist_id, body=body)
            item = await asyncio.to_thread(request.execute)
            return TaskItem(
                id=item["id"],
                title=item.get("title", ""),
                notes=item.get("notes"),
                status=item.get("status", "needsAction"),
                due=_parse_datetime(item.get("due")),
                completed=_parse_datetime(item.get("completed")),
                updated=_parse_datetime(item.get("updated")),
            )
        except RefreshError as e:
            logger.error(
                f"Failed to refresh token for user {user_id}: {e}",
                extra={"json_fields": {"user_id": user_id, "error": str(e)}},
            )
            raise ValueError("Google authorization expired. Please re-authenticate.") from e
        except HttpError as e:
            logger.error(
                f"Google API HTTP error creating task for user {user_id}: {e}",
                extra={"json_fields": {"user_id": user_id, "error": str(e)}},
            )
            raise Exception(f"Google API Error: {e.reason}") from e

    async def update_task(
        self,
        user_id: int,
        db: AsyncSession,
        task_id: str,
        title: str | None = None,
        notes: str | None = None,
        due: datetime | None = None,
        status: str | None = None,
        tasklist_id: str = "@default",
    ) -> TaskItem:
        """
        Update an existing Google Task.

        Args:
            user_id: User ID
            db: Database session
            task_id: Task ID
            title: Updated title
            notes: Updated notes
            due: Updated due date/time
            status: Updated status ('needsAction' or 'completed')
            tasklist_id: Task list ID

        Returns:
            Updated TaskItem
        """
        client = await self._get_tasks_client(user_id, db)

        body: dict[str, Any] = {}
        if title is not None:
            body["title"] = title
        if notes is not None:
            body["notes"] = notes
        if due is not None:
            body["due"] = _format_due_datetime(due)
        if status is not None:
            body["status"] = status

        try:
            request = client.tasks().patch(tasklist=tasklist_id, task=task_id, body=body)
            item = await asyncio.to_thread(request.execute)
            return TaskItem(
                id=item["id"],
                title=item.get("title", ""),
                notes=item.get("notes"),
                status=item.get("status", "needsAction"),
                due=_parse_datetime(item.get("due")),
                completed=_parse_datetime(item.get("completed")),
                updated=_parse_datetime(item.get("updated")),
            )
        except RefreshError as e:
            logger.error(
                f"Failed to refresh token for user {user_id}: {e}",
                extra={"json_fields": {"user_id": user_id, "error": str(e)}},
            )
            raise ValueError("Google authorization expired. Please re-authenticate.") from e
        except HttpError as e:
            logger.error(
                f"Google API HTTP error updating task {task_id} for user {user_id}: {e}",
                extra={"json_fields": {"user_id": user_id, "error": str(e)}},
            )
            raise Exception(f"Google API Error: {e.reason}") from e

    async def complete_task(
        self,
        user_id: int,
        db: AsyncSession,
        task_id: str,
        tasklist_id: str = "@default",
    ) -> TaskItem:
        """
        Mark a task as completed.

        Args:
            user_id: User ID
            db: Database session
            task_id: Task ID
            tasklist_id: Task list ID

        Returns:
            Updated TaskItem
        """
        return await self.update_task(
            user_id=user_id,
            db=db,
            task_id=task_id,
            status="completed",
            tasklist_id=tasklist_id,
        )

    async def delete_task(
        self,
        user_id: int,
        db: AsyncSession,
        task_id: str,
        tasklist_id: str = "@default",
    ) -> bool:
        """
        Delete a task.

        Args:
            user_id: User ID
            db: Database session
            task_id: Task ID
            tasklist_id: Task list ID

        Returns:
            True if successfully deleted
        """
        client = await self._get_tasks_client(user_id, db)

        try:
            request = client.tasks().delete(tasklist=tasklist_id, task=task_id)
            await asyncio.to_thread(request.execute)
            return True
        except RefreshError as e:
            logger.error(
                f"Failed to refresh token for user {user_id}: {e}",
                extra={"json_fields": {"user_id": user_id, "error": str(e)}},
            )
            raise ValueError("Google authorization expired. Please re-authenticate.") from e
        except HttpError as e:
            logger.error(
                f"Google API HTTP error deleting task {task_id} for user {user_id}: {e}",
                extra={"json_fields": {"user_id": user_id, "error": str(e)}},
            )
            raise Exception(f"Google API Error: {e.reason}") from e


    async def handle_google_error(
        self, user_id: int, exception: Exception, db: AsyncSession
    ) -> None:
        """
        Handle Google API errors by updating token status when appropriate.

        Args:
            user_id: The ID of the user
            exception: The caught exception
            db: Database session
        """
        status_val = None
        if isinstance(exception, RefreshError):
            status_val = "expired"
        elif isinstance(exception, HttpError):
            if exception.resp.status in (403, 401):
                try:
                    error_content = json.loads(exception.content.decode("utf-8"))
                    error_obj = error_content.get("error", {})
                    errors = error_obj.get("errors", [])
                    message = error_obj.get("message", "").lower()
                    reasons = [err.get("reason", "") for err in errors]
                    is_scope_error = (
                        "scope" in message
                        or "insufficient" in message
                        or any(
                            r
                            in (
                                "ACCESS_TOKEN_SCOPE_INSUFFICIENT",
                                "insufficientPermissions",
                            )
                            for r in reasons
                        )
                    )
                    if is_scope_error:
                        status_val = "revoked"
                except Exception:
                    if any(
                        phrase in str(exception).lower()
                        for phrase in ("scope", "insufficient", "permission")
                    ):
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
                logger.error(
                    "Failed to update google_token_status for user %s: %s", user_id, e
                )


google_tasks_service_instance = GoogleTasksService()


def google_tasks_service() -> GoogleTasksService:
    """Dependency provider for GoogleTasksService."""
    return google_tasks_service_instance

