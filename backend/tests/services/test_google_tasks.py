from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.tasks import TaskItem, TaskList
from app.services.google_tasks import GoogleTasksService, _format_due_datetime, _parse_datetime


@pytest.fixture
def tasks_service() -> GoogleTasksService:
    return GoogleTasksService()


def test_parse_datetime():
    assert _parse_datetime(None) is None
    parsed = _parse_datetime("2026-07-24T12:00:00.000Z")
    assert parsed is not None
    assert parsed.year == 2026
    assert parsed.month == 7
    assert parsed.day == 24


def test_format_due_datetime():
    assert _format_due_datetime(None) is None
    dt = datetime(2026, 7, 24, 15, 30, tzinfo=timezone.utc)
    formatted = _format_due_datetime(dt)
    assert formatted is not None
    assert "2026-07-24T15:30:00" in formatted


@pytest.mark.asyncio
async def test_get_tasks_client_user_not_found(tasks_service: GoogleTasksService):
    db_mock = AsyncMock()
    with patch("app.services.google_tasks.crud_user.get", return_value=None):
        with pytest.raises(ValueError, match="User with ID 1 not found"):
            await tasks_service._get_tasks_client(1, db_mock)


@pytest.mark.asyncio
async def test_get_tasks_client_no_token(tasks_service: GoogleTasksService):
    db_mock = AsyncMock()
    user_mock = MagicMock()
    user_mock.google_refresh_token = None
    with patch("app.services.google_tasks.crud_user.get", return_value=user_mock):
        with pytest.raises(ValueError, match="has not authorized Google access"):
            await tasks_service._get_tasks_client(1, db_mock)


@pytest.mark.asyncio
async def test_get_task_lists(tasks_service: GoogleTasksService):
    db_mock = AsyncMock()
    mock_client = MagicMock()
    mock_request = MagicMock()
    mock_request.execute.return_value = {
        "items": [
            {"id": "list_1", "title": "My Tasks", "updated": "2026-07-24T10:00:00Z"}
        ]
    }
    mock_client.tasklists().list.return_value = mock_request

    with patch.object(tasks_service, "_get_tasks_client", return_value=mock_client):
        task_lists = await tasks_service.get_task_lists(user_id=1, db=db_mock)
        assert len(task_lists) == 1
        assert task_lists[0].id == "list_1"
        assert task_lists[0].title == "My Tasks"


@pytest.mark.asyncio
async def test_get_tasks(tasks_service: GoogleTasksService):
    db_mock = AsyncMock()
    mock_client = MagicMock()
    mock_request = MagicMock()
    mock_request.execute.return_value = {
        "items": [
            {
                "id": "task_1",
                "title": "Buy Milk",
                "notes": "2% fat",
                "status": "needsAction",
                "due": "2026-07-24T00:00:00.000Z",
            }
        ]
    }
    mock_client.tasks().list.return_value = mock_request

    with patch.object(tasks_service, "_get_tasks_client", return_value=mock_client):
        tasks = await tasks_service.get_tasks(user_id=1, db=db_mock)
        assert len(tasks) == 1
        assert tasks[0].id == "task_1"
        assert tasks[0].title == "Buy Milk"
        assert tasks[0].notes == "2% fat"


@pytest.mark.asyncio
async def test_create_task(tasks_service: GoogleTasksService):
    db_mock = AsyncMock()
    mock_client = MagicMock()
    mock_request = MagicMock()
    mock_request.execute.return_value = {
        "id": "task_new",
        "title": "Call Bob",
        "notes": "Urgent",
        "status": "needsAction",
    }
    mock_client.tasks().insert.return_value = mock_request

    with patch.object(tasks_service, "_get_tasks_client", return_value=mock_client):
        task = await tasks_service.create_task(
            user_id=1, db=db_mock, title="Call Bob", notes="Urgent"
        )
        assert task.id == "task_new"
        assert task.title == "Call Bob"


@pytest.mark.asyncio
async def test_complete_task(tasks_service: GoogleTasksService):
    db_mock = AsyncMock()
    mock_client = MagicMock()
    mock_request = MagicMock()
    mock_request.execute.return_value = {
        "id": "task_1",
        "title": "Buy Milk",
        "status": "completed",
    }
    mock_client.tasks().patch.return_value = mock_request

    with patch.object(tasks_service, "_get_tasks_client", return_value=mock_client):
        task = await tasks_service.complete_task(
            user_id=1, db=db_mock, task_id="task_1"
        )
        assert task.id == "task_1"
        assert task.status == "completed"


@pytest.mark.asyncio
async def test_delete_task(tasks_service: GoogleTasksService):
    db_mock = AsyncMock()
    mock_client = MagicMock()
    mock_request = MagicMock()
    mock_request.execute.return_value = {}
    mock_client.tasks().delete.return_value = mock_request

    with patch.object(tasks_service, "_get_tasks_client", return_value=mock_client):
        res = await tasks_service.delete_task(
            user_id=1, db=db_mock, task_id="task_1"
        )
        assert res is True
