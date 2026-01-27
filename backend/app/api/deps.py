from secrets import compare_digest
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Query, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jwt import PyJWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.crud_user import user as crud_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import TokenPayload
from app.services.google_calendar import (
    GoogleCalendarService,
    google_calendar_service,
)
from app.services.llm import LLMService, llm_service
from app.services.weather import WeatherService, weather_service

SessionDep = Annotated[AsyncSession, Depends(get_db)]
WeatherServiceDep = Annotated[WeatherService, Depends(weather_service)]
LLMServiceDep = Annotated[LLMService, Depends(llm_service)]
CalendarServiceDep = Annotated[GoogleCalendarService, Depends(google_calendar_service)]

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token",
    auto_error=False,
)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    db: SessionDep,
    token: str | None = Depends(reusable_oauth2),
    api_key: str | None = Security(api_key_header),
) -> User:
    """
    Get the current authenticated user.

    Supports two authentication methods:
    1. JWT token via OAuth2 (for user authentication)
    2. API Key via X-API-Key header (for service-to-service communication)

    Args:
        db: Database session
        token: JWT token from Authorization header
        api_key: Optional API key from X-API-Key header

    Returns:
        Authenticated User object

    Raises:
        HTTPException: 401 if authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if api_key and compare_digest(api_key, settings.BACKEND_API_KEY):
        result = await db.execute(select(User).where(User.is_superuser).limit(1))
        system_user = result.scalars().first()
        if system_user:
            return system_user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No system user found for API key authentication",
        )

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenPayload(sub=int(user_id))
    except (PyJWTError, ValueError):
        raise credentials_exception

    user = await crud_user.get(db, id=token_data.sub)
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_superuser(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentSuperUser = Annotated[User, Depends(get_current_active_superuser)]


async def get_target_user_id(
    current_user: CurrentUser,
    user_id: Annotated[
        int | None, Query(description="User ID to fetch events for")
    ] = None,
) -> int:
    if current_user.email == settings.SUPERUSER_EMAIL:
        return user_id or current_user.id
    return current_user.id


TargetUserId = Annotated[int, Depends(get_target_user_id)]
