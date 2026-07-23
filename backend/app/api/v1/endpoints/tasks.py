import logging

from fastapi import APIRouter, HTTPException, Query, status
from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError

from app.api.deps import SessionDep, TargetUserId, TasksServiceDep
from app.schemas.tasks import TaskCreate, TaskItem, TaskList, TasksResponse, TaskUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


def _translate_tasks_exception(e: Exception, *, task_id: str | None = None) -> None:
    if isinstance(e, ValueError):
        error_msg = str(e).lower()
        if "not authorized" in error_msg or "no refresh token" in error_msg or "expired" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            ) from e
        if "failed to create credentials" in error_msg or "failed to build" in error_msg:
            logger.error("Google Tasks client construction failed: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google API error occurred. Please try again later.",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    if isinstance(e, RefreshError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Google access token expired/revoked. Please re-authorize.",
        ) from e
    if isinstance(e, HttpError):
        if e.resp.status == 404 and task_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found.",
            ) from e
        if e.resp.status == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google authentication credentials invalid or expired. Please re-authorize.",
            ) from e
        logger.error("Google Tasks API error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google API error occurred. Please try again later.",
        ) from e
    logger.exception("Unexpected error in Tasks endpoint")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred. Please try again later.",
    ) from e


@router.get("/lists", response_model=list[TaskList])
async def get_task_lists(
    db: SessionDep,
    tasks_service: TasksServiceDep,
    user_id: TargetUserId,
) -> list[TaskList]:
    """Retrieve all Google Task lists for the user."""
    try:
        return await tasks_service.get_task_lists(user_id=user_id, db=db)
    except Exception as e:
        _translate_tasks_exception(e)


@router.get("/", response_model=TasksResponse)
async def get_tasks(
    db: SessionDep,
    tasks_service: TasksServiceDep,
    user_id: TargetUserId,
    tasklist_id: str = Query("@default", description="ID of the task list"),
    show_completed: bool = Query(False, description="Whether to include completed tasks"),
) -> TasksResponse:
    """Retrieve tasks from a Google Task list."""
    try:
        tasks = await tasks_service.get_tasks(
            user_id=user_id,
            db=db,
            tasklist_id=tasklist_id,
            show_completed=show_completed,
        )
        return TasksResponse(tasks=tasks, count=len(tasks))
    except Exception as e:
        _translate_tasks_exception(e)


@router.post("/", response_model=TaskItem, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    db: SessionDep,
    tasks_service: TasksServiceDep,
    user_id: TargetUserId,
) -> TaskItem:
    """Create a new task in Google Tasks."""
    try:
        return await tasks_service.create_task(
            user_id=user_id,
            db=db,
            title=task_in.title,
            notes=task_in.notes,
            due=task_in.due,
            tasklist_id=task_in.tasklist_id,
        )
    except Exception as e:
        _translate_tasks_exception(e)


@router.patch("/{task_id}", response_model=TaskItem)
async def update_task(
    task_id: str,
    task_in: TaskUpdate,
    db: SessionDep,
    tasks_service: TasksServiceDep,
    user_id: TargetUserId,
    tasklist_id: str = Query("@default", description="ID of the task list"),
) -> TaskItem:
    """Update an existing task in Google Tasks."""
    try:
        return await tasks_service.update_task(
            user_id=user_id,
            db=db,
            task_id=task_id,
            title=task_in.title,
            notes=task_in.notes,
            due=task_in.due,
            status=task_in.status,
            tasklist_id=tasklist_id,
        )
    except Exception as e:
        _translate_tasks_exception(e, task_id=task_id)


@router.patch("/{task_id}/complete", response_model=TaskItem)
async def complete_task(
    task_id: str,
    db: SessionDep,
    tasks_service: TasksServiceDep,
    user_id: TargetUserId,
    tasklist_id: str = Query("@default", description="ID of the task list"),
) -> TaskItem:
    """Mark a task as completed."""
    try:
        return await tasks_service.complete_task(
            user_id=user_id,
            db=db,
            task_id=task_id,
            tasklist_id=tasklist_id,
        )
    except Exception as e:
        _translate_tasks_exception(e, task_id=task_id)


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    db: SessionDep,
    tasks_service: TasksServiceDep,
    user_id: TargetUserId,
    tasklist_id: str = Query("@default", description="ID of the task list"),
) -> dict[str, str]:
    """Delete a task from Google Tasks."""
    try:
        await tasks_service.delete_task(
            user_id=user_id,
            db=db,
            task_id=task_id,
            tasklist_id=tasklist_id,
        )
        return {"message": f"Task {task_id} successfully deleted"}
    except Exception as e:
        _translate_tasks_exception(e, task_id=task_id)
