import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.crud.crud_user import user as crud_user
from app.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession) -> None:
    telegram_id = 123456789
    user_in = UserCreate(
        telegram_id=telegram_id,
        full_name="Test User",
        username="testuser",
        timezone="UTC",
        is_superuser=False,
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    assert user.telegram_id == telegram_id
    assert user.full_name == "Test User"
    assert hasattr(user, "id")


@pytest.mark.asyncio
async def test_create_user_with_password(db_session: AsyncSession) -> None:
    """Test that creating a user with a password hashes it correctly."""
    telegram_id = 111222333
    password = "securepassword123"
    user_in = UserCreate(
        telegram_id=telegram_id,
        full_name="Password User",
        username="passworduser",
        email="password@example.com",
        password=password,
        is_superuser=False,
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    assert user.email == "password@example.com"
    assert user.hashed_password is not None
    assert user.hashed_password != password  # Password should be hashed
    assert verify_password(password, user.hashed_password)  # Verify hash works


@pytest.mark.asyncio
async def test_create_user_without_password(db_session: AsyncSession) -> None:
    """Test that creating a user without a password works correctly."""
    telegram_id = 444555666
    user_in = UserCreate(
        telegram_id=telegram_id,
        full_name="No Password User",
        username="nopassworduser",
        email="nopassword@example.com",
        is_superuser=False,
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    assert user.email == "nopassword@example.com"
    assert user.hashed_password is None


@pytest.mark.asyncio
async def test_get_user_by_telegram_id(db_session: AsyncSession) -> None:
    telegram_id = 987654321
    user_in = UserCreate(
        telegram_id=telegram_id,
        full_name="Another User",
        username="anotheruser",
        is_superuser=False,
    )
    await crud_user.create(db_session, obj_in=user_in)

    user = await crud_user.get_by_telegram_id(db_session, telegram_id=telegram_id)
    assert user
    assert user.telegram_id == telegram_id
    assert user.username == "anotheruser"


@pytest.mark.asyncio
async def test_get_user_by_email(db_session: AsyncSession) -> None:
    """Test getting a user by email address."""
    email = "test@example.com"
    user_in = UserCreate(
        telegram_id=777888999,
        full_name="Email User",
        username="emailuser",
        email=email,
        is_superuser=False,
    )
    created_user = await crud_user.create(db_session, obj_in=user_in)

    user = await crud_user.get_by_email(db_session, email=email)
    assert user is not None
    assert user.email == email
    assert user.id == created_user.id


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(db_session: AsyncSession) -> None:
    """Test that getting a non-existent email returns None."""
    user = await crud_user.get_by_email(db_session, email="nonexistent@example.com")
    assert user is None


@pytest.mark.asyncio
async def test_authenticate_user_success(db_session: AsyncSession) -> None:
    """Test successful user authentication with correct credentials."""
    email = "auth@example.com"
    password = "correctpassword"
    user_in = UserCreate(
        telegram_id=123123123,
        full_name="Auth User",
        username="authuser",
        email=email,
        password=password,
        is_superuser=False,
    )
    created_user = await crud_user.create(db_session, obj_in=user_in)

    authenticated_user = await crud_user.authenticate(
        db_session, email=email, password=password
    )
    assert authenticated_user is not None
    assert authenticated_user.id == created_user.id
    assert authenticated_user.email == email


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(db_session: AsyncSession) -> None:
    """Test that authentication fails with incorrect password."""
    email = "wrongpass@example.com"
    password = "correctpassword"
    user_in = UserCreate(
        telegram_id=456456456,
        full_name="Wrong Pass User",
        username="wrongpassuser",
        email=email,
        password=password,
        is_superuser=False,
    )
    await crud_user.create(db_session, obj_in=user_in)

    authenticated_user = await crud_user.authenticate(
        db_session, email=email, password="wrongpassword"
    )
    assert authenticated_user is None


@pytest.mark.asyncio
async def test_authenticate_user_not_found(db_session: AsyncSession) -> None:
    """Test that authentication fails for non-existent user."""
    authenticated_user = await crud_user.authenticate(
        db_session, email="notfound@example.com", password="anypassword"
    )
    assert authenticated_user is None


@pytest.mark.asyncio
async def test_authenticate_user_no_password(db_session: AsyncSession) -> None:
    """Test that authentication fails for user without password."""
    email = "nopass@example.com"
    user_in = UserCreate(
        telegram_id=789789789,
        full_name="No Pass User",
        username="nopassuser",
        email=email,
        is_superuser=False,
        # No password provided
    )
    await crud_user.create(db_session, obj_in=user_in)

    authenticated_user = await crud_user.authenticate(
        db_session, email=email, password="anypassword"
    )
    assert authenticated_user is None


@pytest.mark.asyncio
async def test_get_allowed_telegram_ids(db_session: AsyncSession) -> None:
    telegram_id = 555555555
    user_in = UserCreate(
        telegram_id=telegram_id,
        full_name="Test User",
        username="testuser",
        timezone="UTC",
        is_allowed=True,
        is_superuser=False,
    )
    created_user = await crud_user.create(db_session, obj_in=user_in)
    telegram_ids = await crud_user.get_allowed_telegram_ids(db_session)

    assert len(telegram_ids) == 1
    assert telegram_ids[0]["id"] == created_user.id
    assert telegram_ids[0]["telegram_id"] == telegram_id
