"""Tests for Calendar API endpoints."""

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
from app.schemas.calendar import CalendarEvent
from app.services.google_calendar import google_calendar_service


@pytest.mark.asyncio
async def test_get_today_events_success(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    """Test successful retrieval of today's events."""
    # Use the authenticated user from fixture
    user = auth_user["user"]
    headers = auth_user["headers"]

    # Add Google refresh token to the authenticated user
    await crud_user.update(
        db_session, db_obj=user, obj_in={"google_refresh_token": "test_refresh_token"}
    )

    # Mock calendar service with CalendarEvent objects
    mock_service = AsyncMock()
    mock_service.get_today_events.return_value = [
        CalendarEvent(
            summary="Team Standup",
            start_time=datetime(2026, 1, 26, 9, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 1, 26, 10, 0, 0, tzinfo=timezone.utc),
            is_all_day=False,
            description=None,
            location=None,
        ),
        CalendarEvent(
            summary="Client Meeting",
            start_time=datetime(2026, 1, 26, 14, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 1, 26, 15, 30, 0, tzinfo=timezone.utc),
            is_all_day=False,
            description="Quarterly review",
            location="Conference Room A",
        ),
        CalendarEvent(
            summary="Company Holiday",
            start_time=datetime(2026, 1, 26, 0, 0, 0),
            end_time=None,
            is_all_day=True,
            description=None,
            location=None,
        ),
    ]

    # Override dependency
    async def override_calendar_service():
        return mock_service

    app.dependency_overrides[google_calendar_service] = override_calendar_service

    try:
        response = await client.get(
            f"{settings.API_V1_STR}/calendar/events/today",
            params={"user_id": user.id},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "count" in data
        assert data["count"] == 3
        assert len(data["events"]) == 3

        # Verify event structure
        assert data["events"][0]["summary"] == "Team Standup"
        assert data["events"][0]["is_all_day"] is False
        assert data["events"][1]["summary"] == "Client Meeting"
        assert data["events"][1]["description"] == "Quarterly review"
        assert data["events"][1]["location"] == "Conference Room A"
        assert data["events"][2]["summary"] == "Company Holiday"
        assert data["events"][2]["is_all_day"] is True
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_today_events_no_refresh_token(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    """Test that endpoint returns 401 when user has no refresh token."""
    # Use authenticated user but WITHOUT Google refresh token
    user = auth_user["user"]
    headers = auth_user["headers"]

    response = await client.get(
        f"{settings.API_V1_STR}/calendar/events/today",
        params={"user_id": user.id},
        headers=headers,
    )

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert (
        "not authorized" in data["detail"].lower()
        or "no refresh token" in data["detail"].lower()
    )


@pytest.mark.asyncio
async def test_get_today_events_user_not_found(
    client: AsyncClient, auth_superuser: dict
) -> None:
    """Test that endpoint returns 400 when user doesn't exist (requires superuser)."""
    headers = auth_superuser["headers"]
    non_existent_user_id = 999999

    response = await client.get(
        f"{settings.API_V1_STR}/calendar/events/today",
        params={"user_id": non_existent_user_id},
        headers=headers,
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_get_today_events_expired_token(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    """Test that endpoint returns 403 when refresh token is expired."""
    # Use authenticated user with expired Google refresh token
    user = auth_user["user"]
    headers = auth_user["headers"]

    await crud_user.update(
        db_session, db_obj=user, obj_in={"google_refresh_token": "expired_token"}
    )

    # Mock calendar service to raise RefreshError
    mock_service = AsyncMock()
    mock_service.get_today_events.side_effect = RefreshError("Token expired")

    async def override_calendar_service():
        return mock_service

    app.dependency_overrides[google_calendar_service] = override_calendar_service

    try:
        response = await client.get(
            f"{settings.API_V1_STR}/calendar/events/today",
            params={"user_id": user.id},
            headers=headers,
        )

        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert (
            "expired" in data["detail"].lower()
            or "re-authorize" in data["detail"].lower()
        )
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_today_events_missing_user_id(
    client: AsyncClient, auth_user: dict
) -> None:
    """Test that endpoint works without user_id for regular users (uses current user)."""
    # For regular users, when user_id is not provided, it defaults to current_user.id
    # This should work if the user has a Google refresh token
    headers = auth_user["headers"]

    # Since the user doesn't have a refresh token, it should return 401
    response = await client.get(
        f"{settings.API_V1_STR}/calendar/events/today",
        headers=headers,
    )

    assert response.status_code == 401  # Not authorized (no refresh token)
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_get_upcoming_events_success(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    """Test successful retrieval of upcoming events."""
    # Use authenticated user
    user = auth_user["user"]
    headers = auth_user["headers"]

    await crud_user.update(
        db_session, db_obj=user, obj_in={"google_refresh_token": "test_refresh_token"}
    )

    # Mock calendar service with CalendarEvent objects
    mock_service = AsyncMock()
    mock_service.get_upcoming_events.return_value = [
        CalendarEvent(
            summary="Future Meeting 1",
            start_time=datetime(2026, 1, 27, 10, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 1, 27, 11, 0, 0, tzinfo=timezone.utc),
            is_all_day=False,
            description=None,
            location=None,
        ),
        CalendarEvent(
            summary="Future Meeting 2",
            start_time=datetime(2026, 1, 28, 14, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 1, 28, 15, 0, 0, tzinfo=timezone.utc),
            is_all_day=False,
            description=None,
            location=None,
        ),
    ]

    async def override_calendar_service():
        return mock_service

    app.dependency_overrides[google_calendar_service] = override_calendar_service

    try:
        response = await client.get(
            f"{settings.API_V1_STR}/calendar/events/upcoming",
            params={"user_id": user.id, "days": 7},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "count" in data
        assert data["count"] == 2
        assert len(data["events"]) == 2
        assert data["events"][0]["summary"] == "Future Meeting 1"
        assert data["events"][1]["summary"] == "Future Meeting 2"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_upcoming_events_default_days(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    """Test that upcoming events defaults to 7 days."""
    # Use authenticated user
    user = auth_user["user"]
    headers = auth_user["headers"]

    await crud_user.update(
        db_session, db_obj=user, obj_in={"google_refresh_token": "test_refresh_token"}
    )

    with patch("app.services.google_calendar.build") as mock_build:
        mock_service = MagicMock()
        mock_events_list = MagicMock()
        mock_events_list.execute.return_value = {"items": []}
        mock_service.events.return_value.list.return_value = mock_events_list
        mock_build.return_value = mock_service

        # Don't specify days parameter
        response = await client.get(
            f"{settings.API_V1_STR}/calendar/events/upcoming",
            params={"user_id": user.id},
            headers=headers,
        )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_upcoming_events_invalid_days(
    client: AsyncClient, auth_user: dict
) -> None:
    """Test that days parameter must be between 1 and 30."""
    headers = auth_user["headers"]
    # Test days < 1
    response = await client.get(
        f"{settings.API_V1_STR}/calendar/events/upcoming",
        params={"user_id": 1, "days": 0},
        headers=headers,
    )
    assert response.status_code == 422

    # Test days > 30
    response = await client.get(
        f"{settings.API_V1_STR}/calendar/events/upcoming",
        params={"user_id": 1, "days": 31},
        headers=headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_events_in_range_success(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    """Test successful retrieval of events in custom date range."""
    # Use authenticated user
    user = auth_user["user"]
    headers = auth_user["headers"]

    await crud_user.update(
        db_session, db_obj=user, obj_in={"google_refresh_token": "test_refresh_token"}
    )

    # Mock Google Calendar API response
    mock_events = [
        {
            "summary": "Range Event 1",
            "start": {"dateTime": "2026-02-01T10:00:00Z"},
            "end": {"dateTime": "2026-02-01T11:00:00Z"},
        },
    ]

    with patch("app.services.google_calendar.build") as mock_build:
        mock_service = MagicMock()
        mock_events_list = MagicMock()
        mock_events_list.execute.return_value = {"items": mock_events}
        mock_service.events.return_value.list.return_value = mock_events_list
        mock_build.return_value = mock_service

        start_date = "2026-02-01T00:00:00Z"
        end_date = "2026-02-07T23:59:59Z"

        response = await client.get(
            f"{settings.API_V1_STR}/calendar/events/range",
            params={"user_id": user.id, "start": start_date, "end": end_date},
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert "count" in data
    assert data["count"] == 1


@pytest.mark.asyncio
async def test_get_events_in_range_invalid_range(
    client: AsyncClient, auth_user: dict
) -> None:
    """Test that end date must be after start date."""
    headers = auth_user["headers"]
    start_date = "2026-02-07T00:00:00Z"
    end_date = "2026-02-01T00:00:00Z"  # End before start

    response = await client.get(
        f"{settings.API_V1_STR}/calendar/events/range",
        params={"user_id": 1, "start": start_date, "end": end_date},
        headers=headers,
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "after" in data["detail"].lower()


@pytest.mark.asyncio
async def test_get_events_in_range_exceeds_max_range(
    client: AsyncClient, auth_user: dict
) -> None:
    """Test that date range cannot exceed 365 days."""
    headers = auth_user["headers"]
    start_date = "2026-01-01T00:00:00Z"
    end_date = "2027-01-02T00:00:00Z"  # More than 365 days

    response = await client.get(
        f"{settings.API_V1_STR}/calendar/events/range",
        params={"user_id": 1, "start": start_date, "end": end_date},
        headers=headers,
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "365" in data["detail"]


@pytest.mark.asyncio
async def test_get_events_in_range_missing_parameters(
    client: AsyncClient, auth_user: dict
) -> None:
    """Test that start and end parameters are required."""
    headers = auth_user["headers"]
    # Missing start
    response = await client.get(
        f"{settings.API_V1_STR}/calendar/events/range",
        params={"user_id": 1, "end": "2026-02-01T00:00:00Z"},
        headers=headers,
    )
    assert response.status_code == 422

    # Missing end
    response = await client.get(
        f"{settings.API_V1_STR}/calendar/events/range",
        params={"user_id": 1, "start": "2026-02-01T00:00:00Z"},
        headers=headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_google_api_error_handling(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    """Test that Google API errors are handled properly."""
    # Use authenticated user
    user = auth_user["user"]
    headers = auth_user["headers"]

    await crud_user.update(
        db_session, db_obj=user, obj_in={"google_refresh_token": "test_refresh_token"}
    )

    # Mock calendar service to raise HttpError
    mock_service = AsyncMock()
    mock_service.get_today_events.side_effect = HttpError(
        resp=MagicMock(status=500),
        content=b"Internal Server Error",
    )

    async def override_calendar_service():
        return mock_service

    app.dependency_overrides[google_calendar_service] = override_calendar_service

    try:
        response = await client.get(
            f"{settings.API_V1_STR}/calendar/events/today",
            params={"user_id": user.id},
            headers=headers,
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Google API error" in data["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_empty_events_list(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    """Test that endpoint handles empty events list correctly."""
    # Use authenticated user
    user = auth_user["user"]
    headers = auth_user["headers"]

    await crud_user.update(
        db_session, db_obj=user, obj_in={"google_refresh_token": "test_refresh_token"}
    )

    # Mock empty events response
    with patch("app.services.google_calendar.build") as mock_build:
        mock_service = MagicMock()
        mock_events_list = MagicMock()
        mock_events_list.execute.return_value = {"items": []}
        mock_service.events.return_value.list.return_value = mock_events_list
        mock_build.return_value = mock_service

        response = await client.get(
            f"{settings.API_V1_STR}/calendar/events/today",
            params={"user_id": user.id},
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert len(data["events"]) == 0
