from unittest.mock import AsyncMock, MagicMock

import pytest
from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.crud_user import user as crud_user
from app.main import app
from app.schemas.gmail import EmailMessage
from app.services.gmail_service import gmail_service


@pytest.mark.asyncio
async def test_get_emails_success(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    """Test successful retrieval of email list."""
    user = auth_user["user"]
    headers = auth_user["headers"]

    # Mock user has refresh token
    await crud_user.update(
        db_session, db_obj=user, obj_in={"google_refresh_token": "test_refresh_token"}
    )

    mock_service = AsyncMock()
    mock_service.get_emails.return_value = [
        EmailMessage(
            id="msg1",
            sender="sender1@example.com",
            subject="Invoice details",
            date="Today",
            snippet="Here is your invoice",
            body="Here is your invoice content...",
        ),
        EmailMessage(
            id="msg2",
            sender="sender2@example.com",
            subject="Project status",
            date="Yesterday",
            snippet="Updates for project",
            body="Updates for project content...",
        ),
    ]

    async def override_gmail_service():
        return mock_service

    app.dependency_overrides[gmail_service] = override_gmail_service

    try:
        response = await client.get(
            f"{settings.API_V1_STR}/gmail/messages",
            params={"user_id": user.id, "query": "invoice"},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["emails"]) == 2
        assert data["emails"][0]["id"] == "msg1"
        assert data["emails"][0]["subject"] == "Invoice details"
        mock_service.get_emails.assert_called_with(
            user_id=user.id, db=db_session, query="invoice", max_results=5
        )
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_email_by_id_success(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    """Test successful retrieval of a single email."""
    user = auth_user["user"]
    headers = auth_user["headers"]

    await crud_user.update(
        db_session, db_obj=user, obj_in={"google_refresh_token": "test_refresh_token"}
    )

    mock_service = AsyncMock()
    mock_service.get_email_by_id.return_value = EmailMessage(
        id="msg123",
        sender="sender@example.com",
        subject="Meeting Details",
        date="Today",
        snippet="Short snippet",
        body="Full email body...",
    )

    async def override_gmail_service():
        return mock_service

    app.dependency_overrides[gmail_service] = override_gmail_service

    try:
        response = await client.get(
            f"{settings.API_V1_STR}/gmail/messages/msg123",
            params={"user_id": user.id},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "msg123"
        assert data["subject"] == "Meeting Details"
        assert data["body"] == "Full email body..."
        mock_service.get_email_by_id.assert_called_with(
            user_id=user.id, db=db_session, message_id="msg123"
        )
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_emails_unauthorized(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    """Test retrieval when user has not authorized Google access."""
    user = auth_user["user"]
    headers = auth_user["headers"]

    # Clear refresh token
    await crud_user.update(
        db_session, db_obj=user, obj_in={"google_refresh_token": None}
    )

    mock_service = AsyncMock()
    mock_service.get_emails.side_effect = ValueError("User has not authorized Google access.")

    async def override_gmail_service():
        return mock_service

    app.dependency_overrides[gmail_service] = override_gmail_service

    try:
        response = await client.get(
            f"{settings.API_V1_STR}/gmail/messages",
            params={"user_id": user.id},
            headers=headers,
        )

        assert response.status_code == 401
        assert "not authorized" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_emails_refresh_error(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    """Test get_emails when Google token refresh fails (403 Forbidden)."""
    user = auth_user["user"]
    headers = auth_user["headers"]

    await crud_user.update(
        db_session, db_obj=user, obj_in={"google_refresh_token": "test_refresh_token"}
    )

    mock_service = AsyncMock()
    mock_service.get_emails.side_effect = RefreshError("Token expired")

    async def override_gmail_service():
        return mock_service

    app.dependency_overrides[gmail_service] = override_gmail_service

    try:
        response = await client.get(
            f"{settings.API_V1_STR}/gmail/messages",
            params={"user_id": user.id},
            headers=headers,
        )

        assert response.status_code == 403
        assert "expired/revoked" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_emails_http_error_generic(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    """Test get_emails on non-404 Google API HttpError (500 Internal Error)."""
    user = auth_user["user"]
    headers = auth_user["headers"]

    await crud_user.update(
        db_session, db_obj=user, obj_in={"google_refresh_token": "test_refresh_token"}
    )

    resp = MagicMock()
    resp.status = 502
    resp.reason = "Bad Gateway"
    
    mock_service = AsyncMock()
    mock_service.get_emails.side_effect = HttpError(resp=resp, content=b"Bad Gateway")

    async def override_gmail_service():
        return mock_service

    app.dependency_overrides[gmail_service] = override_gmail_service

    try:
        response = await client.get(
            f"{settings.API_V1_STR}/gmail/messages",
            params={"user_id": user.id},
            headers=headers,
        )

        assert response.status_code == 500
        assert "Google API error occurred" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_email_by_id_http_error_404(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    """Test get_email_by_id when email does not exist (404 Not Found)."""
    user = auth_user["user"]
    headers = auth_user["headers"]

    await crud_user.update(
        db_session, db_obj=user, obj_in={"google_refresh_token": "test_refresh_token"}
    )

    resp = MagicMock()
    resp.status = 404
    resp.reason = "Not Found"
    
    mock_service = AsyncMock()
    mock_service.get_email_by_id.side_effect = HttpError(resp=resp, content=b"Not Found")

    async def override_gmail_service():
        return mock_service

    app.dependency_overrides[gmail_service] = override_gmail_service

    try:
        response = await client.get(
            f"{settings.API_V1_STR}/gmail/messages/msg999",
            params={"user_id": user.id},
            headers=headers,
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_emails_generic_exception(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    """Test get_emails when an unexpected error happens (500)."""
    user = auth_user["user"]
    headers = auth_user["headers"]

    await crud_user.update(
        db_session, db_obj=user, obj_in={"google_refresh_token": "test_refresh_token"}
    )

    mock_service = AsyncMock()
    mock_service.get_emails.side_effect = Exception("System crash")

    async def override_gmail_service():
        return mock_service

    app.dependency_overrides[gmail_service] = override_gmail_service

    try:
        response = await client.get(
            f"{settings.API_V1_STR}/gmail/messages",
            params={"user_id": user.id},
            headers=headers,
        )

        assert response.status_code == 500
        assert "unexpected error occurred" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_emails_bad_request_value_error(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    """Test get_emails when ValueError is raised without auth-related message (400)."""
    user = auth_user["user"]
    headers = auth_user["headers"]

    await crud_user.update(
        db_session, db_obj=user, obj_in={"google_refresh_token": "test_refresh_token"}
    )

    mock_service = AsyncMock()
    mock_service.get_emails.side_effect = ValueError("Invalid query format")

    async def override_gmail_service():
        return mock_service

    app.dependency_overrides[gmail_service] = override_gmail_service

    try:
        response = await client.get(
            f"{settings.API_V1_STR}/gmail/messages",
            params={"user_id": user.id},
            headers=headers,
        )

        assert response.status_code == 400
        assert "invalid query format" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()
