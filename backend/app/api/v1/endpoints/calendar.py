from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, status
from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError

from app.api.deps import CalendarServiceDep, SessionDep, TargetUserId
from app.schemas.calendar import CalendarEventList

router = APIRouter()


@router.get("/events/today", response_model=CalendarEventList)
async def get_today_events(
    db: SessionDep,
    calendar_service: CalendarServiceDep,
    user_id: TargetUserId,
) -> CalendarEventList:
    """
    Get today's calendar events for a specific user.

    Args:
        db: Database session
        calendar_service: Google Calendar service
        user_id: The ID of the user whose events to fetch

    Returns:
        CalendarEventList with formatted event strings

    Raises:
        HTTPException: 401 if user not authenticated with Google
        HTTPException: 403 if refresh token expired/revoked
        HTTPException: 400 for other validation errors
        HTTPException: 500 for Google API errors
    """
    try:
        events = await calendar_service.get_today_events(user_id, db)
        return CalendarEventList(events=events, count=len(events))
    except ValueError as e:
        error_msg = str(e).lower()
        if "not authorized" in error_msg or "no refresh token" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except RefreshError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Google Calendar access expired. Please re-authorize.",
        ) from e
    except HttpError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google API error: {str(e)}",
        ) from e


@router.get("/events/upcoming", response_model=CalendarEventList)
async def get_upcoming_events(
    db: SessionDep,
    calendar_service: CalendarServiceDep,
    user_id: TargetUserId,
    days: int = Query(
        7,
        ge=1,
        le=30,
        description="Number of days to fetch events for (1-30)",
    ),
) -> CalendarEventList:
    """
    Get upcoming calendar events for a specific user.

    Args:
        db: Database session
        calendar_service: Google Calendar service
        user_id: The ID of the user whose events to fetch
        days: Number of days to fetch events for (default: 7, max: 30)

    Returns:
        CalendarEventList with formatted event strings

    Raises:
        HTTPException: 401 if user not authenticated with Google
        HTTPException: 403 if refresh token expired/revoked
        HTTPException: 400 for validation errors
        HTTPException: 500 for Google API errors
    """
    try:
        events = await calendar_service.get_upcoming_events(user_id, db, days)
        return CalendarEventList(events=events, count=len(events))
    except ValueError as e:
        error_msg = str(e).lower()
        if "not authorized" in error_msg or "no refresh token" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except RefreshError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Google Calendar access expired. Please re-authorize.",
        ) from e
    except HttpError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google API error: {str(e)}",
        ) from e


@router.get("/events/range", response_model=CalendarEventList)
async def get_events_in_range(
    db: SessionDep,
    calendar_service: CalendarServiceDep,
    user_id: TargetUserId,
    start: datetime = Query(..., description="Start datetime (ISO 8601)"),
    end: datetime = Query(..., description="End datetime (ISO 8601)"),
) -> CalendarEventList:
    """
    Get calendar events within a specific date range.

    Args:
        db: Database session
        calendar_service: Google Calendar service
        user_id: The ID of the user whose events to fetch
        start: Start datetime in ISO 8601 format
        end: End datetime in ISO 8601 format

    Returns:
        CalendarEventList with formatted event strings

    Raises:
        HTTPException: 401 if user not authenticated with Google
        HTTPException: 403 if refresh token expired/revoked
        HTTPException: 400 for validation errors (invalid date range)
        HTTPException: 500 for Google API errors
    """
    # Validate date range
    if end <= start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end datetime must be after start datetime",
        )

    # Limit range to 365 days
    max_range = timedelta(days=365)
    if (end - start) > max_range:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date range cannot exceed 365 days",
        )

    try:
        events = await calendar_service.get_events_in_range(user_id, start, end, db)
        return CalendarEventList(events=events, count=len(events))
    except ValueError as e:
        error_msg = str(e).lower()
        if "not authorized" in error_msg or "no refresh token" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except RefreshError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Google Calendar access expired. Please re-authorize.",
        ) from e
    except HttpError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google API error: {str(e)}",
        ) from e
