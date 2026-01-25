"""Tests for Google OAuth2 authentication endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.crud_user import user as crud_user
from app.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_google_login_success(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test successful generation of Google OAuth authorization URL."""
    # Create a test user
    user_in = UserCreate(
        telegram_id=111111111,
        full_name="OAuth Test User",
        username="oauthuser",
        email="oauth@example.com",
        is_superuser=False,
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    # Request authorization URL
    response = await client.get(
        f"{settings.API_V1_STR}/google-auth/login",
        params={"user_id": user.id},
    )

    assert response.status_code == 200
    content = response.json()
    assert "authorization_url" in content
    assert "message" in content
    assert "https://accounts.google.com/o/oauth2/auth" in content["authorization_url"]
    assert "calendar.readonly" in content["authorization_url"]
    assert "userinfo.email" in content["authorization_url"]
    assert "access_type=offline" in content["authorization_url"]
    assert "prompt=consent" in content["authorization_url"]
    assert f"state={user.id}" in content["authorization_url"]


@pytest.mark.asyncio
async def test_google_login_missing_user_id(client: AsyncClient) -> None:
    """Test that login endpoint requires user_id parameter."""
    response = await client.get(f"{settings.API_V1_STR}/google-auth/login")

    assert response.status_code == 422  # Validation error
    content = response.json()
    assert "detail" in content


@pytest.mark.asyncio
async def test_google_login_missing_credentials() -> None:
    """Test that login fails when Google OAuth credentials are not configured."""
    from app.services.google_auth import GoogleAuthService

    # Create service instance
    service = GoogleAuthService()

    # Temporarily clear credentials
    original_client_id = settings.GOOGLE_CLIENT_ID
    original_client_secret = settings.GOOGLE_CLIENT_SECRET.get_secret_value()

    try:
        settings.GOOGLE_CLIENT_ID = ""
        settings.GOOGLE_CLIENT_SECRET = ""

        # Should raise ValueError
        with pytest.raises(ValueError, match="Google OAuth credentials not configured"):
            service.get_authorization_url(user_id=1)

    finally:
        # Restore credentials
        settings.GOOGLE_CLIENT_ID = original_client_id
        settings.GOOGLE_CLIENT_SECRET = original_client_secret


@pytest.mark.asyncio
async def test_google_callback_success(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test successful OAuth callback with authorization code."""
    # Create a test user
    user_in = UserCreate(
        telegram_id=222222222,
        full_name="Callback Test User",
        username="callbackuser",
        email="callback@example.com",
        is_superuser=False,
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    # Mock the Google OAuth flow
    mock_credentials = MagicMock()
    mock_credentials.refresh_token = "mock_refresh_token_12345"
    mock_credentials.token = "mock_access_token"

    mock_user_info = {"email": "callback@example.com", "id": "google_user_123"}

    with patch("app.services.google_auth.Flow") as mock_flow_class:
        mock_flow = MagicMock()
        mock_flow.credentials = mock_credentials
        mock_flow_class.from_client_config.return_value = mock_flow

        with patch("googleapiclient.discovery.build") as mock_build:
            mock_service = MagicMock()
            mock_userinfo = MagicMock()
            mock_userinfo.get.return_value.execute.return_value = mock_user_info
            mock_service.userinfo.return_value = mock_userinfo
            mock_build.return_value = mock_service

            # Make callback request
            response = await client.get(
                f"{settings.API_V1_STR}/google-auth/callback",
                params={"code": "mock_auth_code", "state": str(user.id)},
            )

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Authentication Successful" in response.text
    assert "callback@example.com" in response.text

    # Verify refresh token was saved to database
    await db_session.refresh(user)
    assert user.google_refresh_token == "mock_refresh_token_12345"
    assert user.email == "callback@example.com"


@pytest.mark.asyncio
async def test_google_callback_user_denied_access(client: AsyncClient) -> None:
    """Test callback when user denies access."""
    response = await client.get(
        f"{settings.API_V1_STR}/google-auth/callback",
        params={"error": "access_denied", "state": "1"},
    )

    assert response.status_code == 400  # Error parameter present
    assert "text/html" in response.headers["content-type"]
    assert "Authorization Denied" in response.text


@pytest.mark.asyncio
async def test_google_callback_missing_code(client: AsyncClient) -> None:
    """Test callback fails when code parameter is missing."""
    response = await client.get(
        f"{settings.API_V1_STR}/google-auth/callback",
        params={"state": "1"},
    )

    assert response.status_code == 400  # Missing code parameter
    content = response.json()
    assert "detail" in content


@pytest.mark.asyncio
async def test_google_callback_missing_state(client: AsyncClient) -> None:
    """Test callback fails when state parameter is missing."""
    response = await client.get(
        f"{settings.API_V1_STR}/google-auth/callback",
        params={"code": "mock_code"},
    )

    assert response.status_code == 400  # Missing state parameter
    content = response.json()
    assert "detail" in content


@pytest.mark.asyncio
async def test_google_callback_invalid_state(client: AsyncClient) -> None:
    """Test callback fails with invalid state parameter."""
    response = await client.get(
        f"{settings.API_V1_STR}/google-auth/callback",
        params={"code": "mock_code", "state": "invalid_state"},
    )

    assert response.status_code == 400
    content = response.json()
    assert "detail" in content
    assert "Invalid state parameter" in content["detail"]


@pytest.mark.asyncio
async def test_google_callback_user_not_found(client: AsyncClient) -> None:
    """Test callback fails when user doesn't exist."""
    non_existent_user_id = 999999

    response = await client.get(
        f"{settings.API_V1_STR}/google-auth/callback",
        params={"code": "mock_code", "state": str(non_existent_user_id)},
    )

    assert response.status_code == 400
    content = response.json()
    assert "detail" in content
    assert "not found" in content["detail"].lower()


@pytest.mark.asyncio
async def test_google_callback_missing_refresh_token(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test callback fails when Google doesn't return refresh token."""
    # Create a test user
    user_in = UserCreate(
        telegram_id=333333333,
        full_name="No Refresh Token User",
        username="norefreshuser",
        email="norefresh@example.com",
        is_superuser=False,
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    # Mock the Google OAuth flow without refresh token
    mock_credentials = MagicMock()
    mock_credentials.refresh_token = None  # No refresh token
    mock_credentials.token = "mock_access_token"

    with patch("app.services.google_auth.Flow") as mock_flow_class:
        mock_flow = MagicMock()
        mock_flow.credentials = mock_credentials
        mock_flow_class.from_client_config.return_value = mock_flow

        response = await client.get(
            f"{settings.API_V1_STR}/google-auth/callback",
            params={"code": "mock_auth_code", "state": str(user.id)},
        )

    assert response.status_code == 400
    content = response.json()
    assert "detail" in content
    assert "No refresh token" in content["detail"]


@pytest.mark.asyncio
async def test_google_callback_google_api_error(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test callback handles Google API errors gracefully."""
    # Create a test user
    user_in = UserCreate(
        telegram_id=444444444,
        full_name="API Error User",
        username="apierroruser",
        email="apierror@example.com",
        is_superuser=False,
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    # Mock the Google OAuth flow to raise an exception
    with patch("app.services.google_auth.Flow") as mock_flow_class:
        mock_flow = MagicMock()
        mock_flow.fetch_token.side_effect = Exception("Google API error")
        mock_flow_class.from_client_config.return_value = mock_flow

        response = await client.get(
            f"{settings.API_V1_STR}/google-auth/callback",
            params={"code": "mock_auth_code", "state": str(user.id)},
        )

    assert response.status_code == 500
    content = response.json()
    assert "detail" in content
    assert "Internal Server Error" in content["detail"]


@pytest.mark.asyncio
async def test_google_auth_service_exchange_code_updates_user(
    db_session: AsyncSession,
) -> None:
    """Test that exchange_code_for_token properly updates user in database."""
    from app.services.google_auth import google_auth_service

    # Create a test user
    user_in = UserCreate(
        telegram_id=555555555,
        full_name="Service Test User",
        username="serviceuser",
        email="old@example.com",
        is_superuser=False,
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    # Mock the Google OAuth flow
    mock_credentials = MagicMock()
    mock_credentials.refresh_token = "new_refresh_token_xyz"
    mock_credentials.token = "new_access_token"

    mock_user_info = {"email": "new@example.com", "id": "google_123"}

    with patch("app.services.google_auth.Flow") as mock_flow_class:
        mock_flow = MagicMock()
        mock_flow.credentials = mock_credentials
        mock_flow_class.from_client_config.return_value = mock_flow

        with patch("googleapiclient.discovery.build") as mock_build:
            mock_service = MagicMock()
            mock_userinfo = MagicMock()
            mock_userinfo.get.return_value.execute.return_value = mock_user_info
            mock_service.userinfo.return_value = mock_userinfo
            mock_build.return_value = mock_service

            # Call the service method
            result = await google_auth_service.exchange_code_for_token(
                code="test_code", state=str(user.id), db=db_session
            )

    # Verify result
    assert result["message"] == "Successfully authenticated with Google"
    assert result["email"] == "new@example.com"
    assert result["user_id"] == user.id

    # Verify database was updated
    await db_session.refresh(user)
    assert user.google_refresh_token == "new_refresh_token_xyz"
    assert user.email == "new@example.com"


@pytest.mark.asyncio
async def test_google_auth_preserves_existing_auth(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that Google OAuth doesn't interfere with existing JWT authentication."""
    # Create a user with password
    user_in = UserCreate(
        telegram_id=666666666,
        full_name="Dual Auth User",
        username="dualauthuser",
        email="dualauth@example.com",
        password="testpassword123",
        is_superuser=False,
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    # Test JWT login still works
    login_data = {
        "username": "dualauth@example.com",
        "password": "testpassword123",
    }
    response = await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data=login_data,
    )

    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data

    # Now add Google OAuth
    mock_credentials = MagicMock()
    mock_credentials.refresh_token = "google_refresh_token"
    mock_credentials.token = "google_access_token"

    mock_user_info = {"email": "dualauth@example.com", "id": "google_456"}

    with patch("app.services.google_auth.Flow") as mock_flow_class:
        mock_flow = MagicMock()
        mock_flow.credentials = mock_credentials
        mock_flow_class.from_client_config.return_value = mock_flow

        with patch("googleapiclient.discovery.build") as mock_build:
            mock_service = MagicMock()
            mock_userinfo = MagicMock()
            mock_userinfo.get.return_value.execute.return_value = mock_user_info
            mock_service.userinfo.return_value = mock_userinfo
            mock_build.return_value = mock_service

            response = await client.get(
                f"{settings.API_V1_STR}/google-auth/callback",
                params={"code": "mock_code", "state": str(user.id)},
            )

    assert response.status_code == 200

    # Verify JWT login still works after Google OAuth
    response = await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data=login_data,
    )

    assert response.status_code == 200
    assert "access_token" in response.json()

    # Verify user has both authentication methods
    await db_session.refresh(user)
    assert user.hashed_password is not None  # JWT auth still works
    assert user.google_refresh_token == "google_refresh_token"  # Google OAuth added
