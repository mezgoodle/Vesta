from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.crud_user import user as crud_user
from app.main import app
from app.schemas.tasks import TaskItem, TaskList
from app.services.google_tasks import google_tasks_service


@pytest.mark.asyncio
async def test_get_task_lists_endpoint(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    user = auth_user["user"]
    headers = auth_user["headers"]

    await crud_user.update(
        db_session, db_obj=user, obj_in={"google_refresh_token": "valid_token"}
    )

    mock_service = AsyncMock()
    mock_service.get_task_lists.return_value = [TaskList(id="list_1", title="My Tasks")]

    async def override_tasks_service():
        return mock_service

    app.dependency_overrides[google_tasks_service] = override_tasks_service

    try:
        response = await client.get(
            f"{settings.API_V1_STR}/tasks/lists",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "list_1"
        assert data[0]["title"] == "My Tasks"
    finally:
        app.dependency_overrides.pop(google_tasks_service, None)


@pytest.mark.asyncio
async def test_get_tasks_endpoint(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    user = auth_user["user"]
    headers = auth_user["headers"]

    await crud_user.update(
        db_session, db_obj=user, obj_in={"google_refresh_token": "valid_token"}
    )

    mock_service = AsyncMock()
    mock_service.get_tasks.return_value = [
        TaskItem(id="task_1", title="Buy Groceries", status="needsAction")
    ]

    async def override_tasks_service():
        return mock_service

    app.dependency_overrides[google_tasks_service] = override_tasks_service

    try:
        response = await client.get(
            f"{settings.API_V1_STR}/tasks/",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["tasks"][0]["title"] == "Buy Groceries"
    finally:
        app.dependency_overrides.pop(google_tasks_service, None)


@pytest.mark.asyncio
async def test_create_task_endpoint(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    user = auth_user["user"]
    headers = auth_user["headers"]

    await crud_user.update(
        db_session, db_obj=user, obj_in={"google_refresh_token": "valid_token"}
    )

    mock_service = AsyncMock()
    mock_service.create_task.return_value = TaskItem(
        id="task_new", title="New Task", notes="Some details"
    )

    async def override_tasks_service():
        return mock_service

    app.dependency_overrides[google_tasks_service] = override_tasks_service

    try:
        response = await client.post(
            f"{settings.API_V1_STR}/tasks/",
            json={"title": "New Task", "notes": "Some details"},
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "task_new"
        assert data["title"] == "New Task"
    finally:
        app.dependency_overrides.pop(google_tasks_service, None)


@pytest.mark.asyncio
async def test_complete_task_endpoint(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    user = auth_user["user"]
    headers = auth_user["headers"]

    await crud_user.update(
        db_session, db_obj=user, obj_in={"google_refresh_token": "valid_token"}
    )

    mock_service = AsyncMock()
    mock_service.complete_task.return_value = TaskItem(
        id="task_1", title="Task 1", status="completed"
    )

    async def override_tasks_service():
        return mock_service

    app.dependency_overrides[google_tasks_service] = override_tasks_service

    try:
        response = await client.patch(
            f"{settings.API_V1_STR}/tasks/task_1/complete",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
    finally:
        app.dependency_overrides.pop(google_tasks_service, None)


@pytest.mark.asyncio
async def test_delete_task_endpoint(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    user = auth_user["user"]
    headers = auth_user["headers"]

    await crud_user.update(
        db_session, db_obj=user, obj_in={"google_refresh_token": "valid_token"}
    )

    mock_service = AsyncMock()
    mock_service.delete_task.return_value = True

    async def override_tasks_service():
        return mock_service

    app.dependency_overrides[google_tasks_service] = override_tasks_service

    try:
        response = await client.delete(
            f"{settings.API_V1_STR}/tasks/task_1",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "successfully deleted" in data["message"]
    finally:
        app.dependency_overrides.pop(google_tasks_service, None)


@pytest.mark.asyncio
async def test_update_task_endpoint(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    user = auth_user["user"]
    headers = auth_user["headers"]

    await crud_user.update(
        db_session, db_obj=user, obj_in={"google_refresh_token": "valid_token"}
    )

    mock_service = AsyncMock()
    mock_service.update_task.return_value = TaskItem(
        id="task_1", title="Updated Title", notes="Updated notes", status="needsAction"
    )

    async def override_tasks_service():
        return mock_service

    app.dependency_overrides[google_tasks_service] = override_tasks_service

    try:
        response = await client.patch(
            f"{settings.API_V1_STR}/tasks/task_1",
            json={"title": "Updated Title", "notes": "Updated notes"},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "task_1"
        assert data["title"] == "Updated Title"
        assert data["notes"] == "Updated notes"
    finally:
        app.dependency_overrides.pop(google_tasks_service, None)
