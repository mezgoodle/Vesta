from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.crud_user import user as crud_user
from app.main import app
from app.schemas.calendar import CalendarEventCreate
from app.services.google_calendar import google_calendar_service

@pytest.mark.asyncio
async def test_get_today_events_value_error(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    user = auth_user["user"]
    headers = auth_user["headers"]

    await crud_user.update(
        db_session, db_obj=user, obj_in={"google_refresh_token": "test_refresh_token"}
    )

    mock_service = AsyncMock()
    mock_service.get_today_events.side_effect = ValueError("Some other error")

    async def override_calendar_service():
        return mock_service

    app.dependency_overrides[google_calendar_service] = override_calendar_service

    try:
        response = await client.get(
            f"{settings.API_V1_STR}/calendar/events/today",
            params={"user_id": user.id},
            headers=headers,
        )

        assert response.status_code == 400
        assert "Some other error" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_upcoming_events_value_error_unauth(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    user = auth_user["user"]
    headers = auth_user["headers"]

    mock_service = AsyncMock()
    mock_service.get_upcoming_events.side_effect = ValueError("not authorized")

    async def override_calendar_service():
        return mock_service

    app.dependency_overrides[google_calendar_service] = override_calendar_service

    try:
        response = await client.get(
            f"{settings.API_V1_STR}/calendar/events/upcoming",
            params={"user_id": user.id, "days": 7},
            headers=headers,
        )

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_upcoming_events_value_error_other(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    user = auth_user["user"]
    headers = auth_user["headers"]

    mock_service = AsyncMock()
    mock_service.get_upcoming_events.side_effect = ValueError("other error")

    async def override_calendar_service():
        return mock_service

    app.dependency_overrides[google_calendar_service] = override_calendar_service

    try:
        response = await client.get(
            f"{settings.API_V1_STR}/calendar/events/upcoming",
            params={"user_id": user.id, "days": 7},
            headers=headers,
        )

        assert response.status_code == 400
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_upcoming_events_refresh_error(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    user = auth_user["user"]
    headers = auth_user["headers"]

    mock_service = AsyncMock()
    mock_service.get_upcoming_events.side_effect = RefreshError("refresh error")

    async def override_calendar_service():
        return mock_service

    app.dependency_overrides[google_calendar_service] = override_calendar_service

    try:
        response = await client.get(
            f"{settings.API_V1_STR}/calendar/events/upcoming",
            params={"user_id": user.id, "days": 7},
            headers=headers,
        )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_upcoming_events_http_error(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    user = auth_user["user"]
    headers = auth_user["headers"]

    mock_service = AsyncMock()
    mock_service.get_upcoming_events.side_effect = HttpError(resp=MagicMock(status=500), content=b"error")

    async def override_calendar_service():
        return mock_service

    app.dependency_overrides[google_calendar_service] = override_calendar_service

    try:
        response = await client.get(
            f"{settings.API_V1_STR}/calendar/events/upcoming",
            params={"user_id": user.id, "days": 7},
            headers=headers,
        )

        assert response.status_code == 500
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_events_in_range_value_error_unauth(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    user = auth_user["user"]
    headers = auth_user["headers"]

    mock_service = AsyncMock()
    mock_service.get_events_in_range.side_effect = ValueError("no refresh token")

    async def override_calendar_service():
        return mock_service

    app.dependency_overrides[google_calendar_service] = override_calendar_service

    try:
        start_date = "2026-02-01T00:00:00Z"
        end_date = "2026-02-07T23:59:59Z"
        response = await client.get(
            f"{settings.API_V1_STR}/calendar/events/range",
            params={"user_id": user.id, "start": start_date, "end": end_date},
            headers=headers,
        )

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_events_in_range_value_error_other(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    user = auth_user["user"]
    headers = auth_user["headers"]

    mock_service = AsyncMock()
    mock_service.get_events_in_range.side_effect = ValueError("other error")

    async def override_calendar_service():
        return mock_service

    app.dependency_overrides[google_calendar_service] = override_calendar_service

    try:
        start_date = "2026-02-01T00:00:00Z"
        end_date = "2026-02-07T23:59:59Z"
        response = await client.get(
            f"{settings.API_V1_STR}/calendar/events/range",
            params={"user_id": user.id, "start": start_date, "end": end_date},
            headers=headers,
        )

        assert response.status_code == 400
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_events_in_range_refresh_error(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    user = auth_user["user"]
    headers = auth_user["headers"]

    mock_service = AsyncMock()
    mock_service.get_events_in_range.side_effect = RefreshError("refresh error")

    async def override_calendar_service():
        return mock_service

    app.dependency_overrides[google_calendar_service] = override_calendar_service

    try:
        start_date = "2026-02-01T00:00:00Z"
        end_date = "2026-02-07T23:59:59Z"
        response = await client.get(
            f"{settings.API_V1_STR}/calendar/events/range",
            params={"user_id": user.id, "start": start_date, "end": end_date},
            headers=headers,
        )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_events_in_range_http_error(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    user = auth_user["user"]
    headers = auth_user["headers"]

    mock_service = AsyncMock()
    mock_service.get_events_in_range.side_effect = HttpError(resp=MagicMock(status=500), content=b"error")

    async def override_calendar_service():
        return mock_service

    app.dependency_overrides[google_calendar_service] = override_calendar_service

    try:
        start_date = "2026-02-01T00:00:00Z"
        end_date = "2026-02-07T23:59:59Z"
        response = await client.get(
            f"{settings.API_V1_STR}/calendar/events/range",
            params={"user_id": user.id, "start": start_date, "end": end_date},
            headers=headers,
        )

        assert response.status_code == 500
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_calendar_event_success(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    user = auth_user["user"]
    headers = auth_user["headers"]

    await crud_user.update(
        db_session, db_obj=user, obj_in={"google_refresh_token": "test_refresh_token"}
    )

    mock_service = AsyncMock()
    mock_service.create_event.return_value = {
        "summary": "New Event",
        "html_link": "http://link",
        "start_time": datetime(2026, 2, 1, 10, 0, tzinfo=timezone.utc),
        "end_time": datetime(2026, 2, 1, 11, 0, tzinfo=timezone.utc),
        "is_all_day": False
    }

    async def override_calendar_service():
        return mock_service

    app.dependency_overrides[google_calendar_service] = override_calendar_service

    try:
        event_data = {
            "summary": "New Event",
            "start_time": "2026-02-01T10:00:00Z",
            "end_time": "2026-02-01T11:00:00Z",
        }
        response = await client.post(
            f"{settings.API_V1_STR}/calendar/events",
            params={"user_id": user.id},
            json=event_data,
            headers=headers,
        )

        assert response.status_code == 201
        assert response.json()["html_link"] == "http://link"
        assert response.json()["summary"] == "New Event"
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_calendar_event_value_error_unauth(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    user = auth_user["user"]
    headers = auth_user["headers"]

    mock_service = AsyncMock()
    mock_service.create_event.side_effect = ValueError("not authorized")

    async def override_calendar_service():
        return mock_service

    app.dependency_overrides[google_calendar_service] = override_calendar_service

    try:
        event_data = {
            "summary": "New Event",
            "start_time": "2026-02-01T10:00:00Z",
            "end_time": "2026-02-01T11:00:00Z",
        }
        response = await client.post(
            f"{settings.API_V1_STR}/calendar/events",
            params={"user_id": user.id},
            json=event_data,
            headers=headers,
        )

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_calendar_event_value_error_other(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    user = auth_user["user"]
    headers = auth_user["headers"]

    mock_service = AsyncMock()
    mock_service.create_event.side_effect = ValueError("other error")

    async def override_calendar_service():
        return mock_service

    app.dependency_overrides[google_calendar_service] = override_calendar_service

    try:
        event_data = {
            "summary": "New Event",
            "start_time": "2026-02-01T10:00:00Z",
            "end_time": "2026-02-01T11:00:00Z",
        }
        response = await client.post(
            f"{settings.API_V1_STR}/calendar/events",
            params={"user_id": user.id},
            json=event_data,
            headers=headers,
        )

        assert response.status_code == 400
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_calendar_event_refresh_error(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    user = auth_user["user"]
    headers = auth_user["headers"]

    mock_service = AsyncMock()
    mock_service.create_event.side_effect = RefreshError("refresh error")

    async def override_calendar_service():
        return mock_service

    app.dependency_overrides[google_calendar_service] = override_calendar_service

    try:
        event_data = {
            "summary": "New Event",
            "start_time": "2026-02-01T10:00:00Z",
            "end_time": "2026-02-01T11:00:00Z",
        }
        response = await client.post(
            f"{settings.API_V1_STR}/calendar/events",
            params={"user_id": user.id},
            json=event_data,
            headers=headers,
        )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_calendar_event_http_error(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    user = auth_user["user"]
    headers = auth_user["headers"]

    mock_service = AsyncMock()
    mock_service.create_event.side_effect = HttpError(resp=MagicMock(status=500), content=b"error")

    async def override_calendar_service():
        return mock_service

    app.dependency_overrides[google_calendar_service] = override_calendar_service

    try:
        event_data = {
            "summary": "New Event",
            "start_time": "2026-02-01T10:00:00Z",
            "end_time": "2026-02-01T11:00:00Z",
        }
        response = await client.post(
            f"{settings.API_V1_STR}/calendar/events",
            params={"user_id": user.id},
            json=event_data,
            headers=headers,
        )

        assert response.status_code == 500
    finally:
        app.dependency_overrides.clear()
