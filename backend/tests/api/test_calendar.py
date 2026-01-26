"""Tests for Calendar API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.crud_user import user as crud_user
from app.main import app
from app.schemas.user import UserCreate
from app.services.google_calendar import google_calendar_service


@pytest.mark.asyncio
async def test_get_today_events_success(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test successful retrieval of today's events."""
    # Create a test user with Google refresh token
    user_in = UserCreate(
        telegram_id=111111111,
        full_name="Calendar Test User",
        username="calendaruser",
        email="calendar@example.com",
        is_superuser=False,
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    # Add Google refresh token
    await crud_user.update(
        db_session, db_obj=user, obj_in={"google_refresh_token": "test_refresh_token"}
    )

    # Mock calendar service
    mock_service = AsyncMock()
    mock_service.get_today_events.return_value = [
        "09:00 - 10:00: Team Standup",
        "14:00 - 15:30: Client Meeting",
        "All day: Company Holiday",
    ]

    # Override dependency
    async def override_calendar_service():
        return mock_service

    app.dependency_overrides[google_calendar_service] = override_calendar_service

    try:
        response = await client.get(
            f"{settings.API_V1_STR}/calendar/events/today",
            params={"user_id": user.id},
        )

        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "count" in data
        assert data["count"] == 3
        assert len(data["events"]) == 3
        assert "09:00 - 10:00: Team Standup" in data["events"]
        assert "14:00 - 15:30: Client Meeting" in data["events"]
        assert "All day: Company Holiday" in data["events"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_today_events_no_refresh_token(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that endpoint returns 401 when user has no refresh token."""
    # Create a test user WITHOUT Google refresh token
    user_in = UserCreate(
        telegram_id=222222222,
        full_name="No Token User",
        username="notokenuser",
        email="notoken@example.com",
        is_superuser=False,
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    response = await client.get(
        f"{settings.API_V1_STR}/calendar/events/today",
        params={"user_id": user.id},
    )

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "not authorized" in data["detail"].lower()


@pytest.mark.asyncio
async def test_get_today_events_user_not_found(client: AsyncClient) -> None:
    """Test that endpoint returns 400 when user doesn't exist."""
    non_existent_user_id = 999999

    response = await client.get(
        f"{settings.API_V1_STR}/calendar/events/today",
        params={"user_id": non_existent_user_id},
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_get_today_events_expired_token(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that endpoint returns 403 when refresh token is expired."""
    # Create a test user with Google refresh token
    user_in = UserCreate(
        telegram_id=333333333,
        full_name="Expired Token User",
        username="expireduser",
        email="expired@example.com",
        is_superuser=False,
    )
    user = await crud_user.create(db_session, obj_in=user_in)

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
async def test_get_today_events_missing_user_id(client: AsyncClient) -> None:
    """Test that endpoint requires user_id parameter."""
    response = await client.get(f"{settings.API_V1_STR}/calendar/events/today")

    assert response.status_code == 422  # Validation error
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_get_upcoming_events_success(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test successful retrieval of upcoming events."""
    # Create a test user with Google refresh token
    user_in = UserCreate(
        telegram_id=444444444,
        full_name="Upcoming Events User",
        username="upcominguser",
        email="upcoming@example.com",
        is_superuser=False,
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    await crud_user.update(
        db_session, db_obj=user, obj_in={"google_refresh_token": "test_refresh_token"}
    )

    # Mock calendar service
    mock_service = AsyncMock()
    mock_service.get_upcoming_events.return_value = [
        "10:00 - 11:00: Future Meeting 1",
        "14:00 - 15:00: Future Meeting 2",
    ]

    async def override_calendar_service():
        return mock_service

    app.dependency_overrides[google_calendar_service] = override_calendar_service

    try:
        response = await client.get(
            f"{settings.API_V1_STR}/calendar/events/upcoming",
            params={"user_id": user.id, "days": 7},
        )

        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "count" in data
        assert data["count"] == 2
        assert len(data["events"]) == 2
        assert "10:00 - 11:00: Future Meeting 1" in data["events"]
        assert "14:00 - 15:00: Future Meeting 2" in data["events"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_upcoming_events_default_days(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that upcoming events defaults to 7 days."""
    # Create a test user with Google refresh token
    user_in = UserCreate(
        telegram_id=555555555,
        full_name="Default Days User",
        username="defaultuser",
        email="default@example.com",
        is_superuser=False,
    )
    user = await crud_user.create(db_session, obj_in=user_in)

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
        )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_upcoming_events_invalid_days(client: AsyncClient) -> None:
    """Test that days parameter must be between 1 and 30."""
    # Test days < 1
    response = await client.get(
        f"{settings.API_V1_STR}/calendar/events/upcoming",
        params={"user_id": 1, "days": 0},
    )
    assert response.status_code == 422

    # Test days > 30
    response = await client.get(
        f"{settings.API_V1_STR}/calendar/events/upcoming",
        params={"user_id": 1, "days": 31},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_events_in_range_success(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test successful retrieval of events in custom date range."""
    # Create a test user with Google refresh token
    user_in = UserCreate(
        telegram_id=666666666,
        full_name="Range Events User",
        username="rangeuser",
        email="range@example.com",
        is_superuser=False,
    )
    user = await crud_user.create(db_session, obj_in=user_in)

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
        )

    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert "count" in data
    assert data["count"] == 1


@pytest.mark.asyncio
async def test_get_events_in_range_invalid_range(client: AsyncClient) -> None:
    """Test that end date must be after start date."""
    start_date = "2026-02-07T00:00:00Z"
    end_date = "2026-02-01T00:00:00Z"  # End before start

    response = await client.get(
        f"{settings.API_V1_STR}/calendar/events/range",
        params={"user_id": 1, "start": start_date, "end": end_date},
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "after" in data["detail"].lower()


@pytest.mark.asyncio
async def test_get_events_in_range_exceeds_max_range(client: AsyncClient) -> None:
    """Test that date range cannot exceed 365 days."""
    start_date = "2026-01-01T00:00:00Z"
    end_date = "2027-01-02T00:00:00Z"  # More than 365 days

    response = await client.get(
        f"{settings.API_V1_STR}/calendar/events/range",
        params={"user_id": 1, "start": start_date, "end": end_date},
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "365" in data["detail"]


@pytest.mark.asyncio
async def test_get_events_in_range_missing_parameters(client: AsyncClient) -> None:
    """Test that start and end parameters are required."""
    # Missing start
    response = await client.get(
        f"{settings.API_V1_STR}/calendar/events/range",
        params={"user_id": 1, "end": "2026-02-01T00:00:00Z"},
    )
    assert response.status_code == 422

    # Missing end
    response = await client.get(
        f"{settings.API_V1_STR}/calendar/events/range",
        params={"user_id": 1, "start": "2026-02-01T00:00:00Z"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_google_api_error_handling(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that Google API errors are handled properly."""
    # Create a test user with Google refresh token
    user_in = UserCreate(
        telegram_id=777777777,
        full_name="API Error User",
        username="apierroruser",
        email="apierror@example.com",
        is_superuser=False,
    )
    user = await crud_user.create(db_session, obj_in=user_in)

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
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Google API error" in data["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_empty_events_list(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test that endpoint handles empty events list correctly."""
    # Create a test user with Google refresh token
    user_in = UserCreate(
        telegram_id=888888888,
        full_name="No Events User",
        username="noeventsuser",
        email="noevents@example.com",
        is_superuser=False,
    )
    user = await crud_user.create(db_session, obj_in=user_in)

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
        )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert len(data["events"]) == 0
