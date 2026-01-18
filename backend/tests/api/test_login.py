import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.crud_user import user as crud_user
from app.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_login_access_token_success(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test successful login with correct credentials."""
    email = "login@example.com"
    password = "testpassword123"

    # Create a user with email and password
    user_in = UserCreate(
        telegram_id=111111111,
        full_name="Login User",
        username="loginuser",
        email=email,
        password=password,
        is_superuser=False,
    )
    await crud_user.create(db_session, obj_in=user_in)

    # Attempt to login
    login_data = {
        "username": email,  # OAuth2 uses 'username' field for email
        "password": password,
    }
    response = await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data=login_data,
    )

    assert response.status_code == 200
    content = response.json()
    assert "access_token" in content
    assert content["token_type"] == "bearer"
    assert len(content["access_token"]) > 0


@pytest.mark.asyncio
async def test_login_access_token_wrong_password(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test login fails with incorrect password."""
    email = "wrongpass@example.com"
    password = "correctpassword"

    # Create a user
    user_in = UserCreate(
        telegram_id=222222222,
        full_name="Wrong Pass User",
        username="wrongpassuser",
        email=email,
        password=password,
        is_superuser=False,
    )
    await crud_user.create(db_session, obj_in=user_in)

    # Attempt to login with wrong password
    login_data = {
        "username": email,
        "password": "wrongpassword",
    }
    response = await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data=login_data,
    )

    assert response.status_code == 401
    content = response.json()
    assert "detail" in content
    assert "incorrect" in content["detail"].lower()


@pytest.mark.asyncio
async def test_login_access_token_user_not_found(client: AsyncClient) -> None:
    """Test login fails for non-existent user."""
    login_data = {
        "username": "nonexistent@example.com",
        "password": "anypassword",
    }
    response = await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data=login_data,
    )

    assert response.status_code == 401
    content = response.json()
    assert "detail" in content
    assert "incorrect" in content["detail"].lower()


@pytest.mark.asyncio
async def test_login_access_token_user_without_password(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test login fails for user without password (e.g., Telegram-only user)."""
    email = "nopassword@example.com"

    # Create a user without password
    user_in = UserCreate(
        telegram_id=333333333,
        full_name="No Password User",
        username="nopassworduser",
        email=email,
        is_superuser=False,
        # No password provided
    )
    await crud_user.create(db_session, obj_in=user_in)

    # Attempt to login
    login_data = {
        "username": email,
        "password": "anypassword",
    }
    response = await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data=login_data,
    )

    assert response.status_code == 401
    content = response.json()
    assert "detail" in content


@pytest.mark.asyncio
async def test_login_access_token_missing_credentials(client: AsyncClient) -> None:
    """Test login fails with missing credentials."""
    # Missing password
    response = await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": "test@example.com"},
    )
    assert response.status_code == 422  # Validation error

    # Missing username
    response = await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"password": "testpassword"},
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_login_access_token_empty_credentials(client: AsyncClient) -> None:
    """Test login fails with empty credentials."""
    login_data = {
        "username": "",
        "password": "",
    }
    response = await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data=login_data,
    )

    # Should fail - either 401 or 422 depending on validation
    assert response.status_code in [401, 422]


@pytest.mark.asyncio
async def test_login_access_token_creates_valid_jwt(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that the returned token is a valid JWT that can be used for authentication."""
    email = "jwttest@example.com"
    password = "jwtpassword123"

    # Create a user
    user_in = UserCreate(
        telegram_id=444444444,
        full_name="JWT Test User",
        username="jwttestuser",
        email=email,
        password=password,
        is_superuser=False,
    )
    await crud_user.create(db_session, obj_in=user_in)

    # Login to get token
    login_data = {
        "username": email,
        "password": password,
    }
    response = await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data=login_data,
    )

    assert response.status_code == 200
    token_data = response.json()
    access_token = token_data["access_token"]

    # Use the token to access a protected endpoint (if you have one)
    # For now, we'll just verify the token structure
    assert access_token is not None
    assert len(access_token.split(".")) == 3  # JWT has 3 parts separated by dots


@pytest.mark.asyncio
async def test_login_access_token_superuser(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that superusers can also login successfully."""
    email = "admin@example.com"
    password = "adminpassword123"

    # Create a superuser
    user_in = UserCreate(
        telegram_id=555555555,
        full_name="Admin User",
        username="adminuser",
        email=email,
        password=password,
        is_superuser=True,
    )
    await crud_user.create(db_session, obj_in=user_in)

    # Login
    login_data = {
        "username": email,
        "password": password,
    }
    response = await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data=login_data,
    )

    assert response.status_code == 200
    content = response.json()
    assert "access_token" in content
    assert content["token_type"] == "bearer"
