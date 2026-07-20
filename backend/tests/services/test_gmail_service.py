import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.auth.exceptions import RefreshError

from app.services.gmail_service import GmailService


@pytest.fixture
def gmail_service():
    return GmailService()


def test_extract_body_plain_text(gmail_service):
    # Simple plain text body
    data = base64.urlsafe_b64encode(b"Hello World").decode("utf-8")
    payload = {
        "mimeType": "text/plain",
        "body": {"data": data},
    }
    body = gmail_service._extract_body(payload)
    assert body == "Hello World"


def test_extract_body_html_only(gmail_service):
    # Simple HTML body, parsed with BeautifulSoup
    html_content = (
        "<html><body><h1>Hello World</h1><style>p {color: red;}</style></body></html>"
    )
    data = base64.urlsafe_b64encode(html_content.encode("utf-8")).decode("utf-8")
    payload = {
        "mimeType": "text/html",
        "body": {"data": data},
    }
    body = gmail_service._extract_body(payload)
    assert "Hello World" in body
    assert "style" not in body


def test_extract_body_multipart(gmail_service):
    # Multipart body with both text and HTML
    plain_data = base64.urlsafe_b64encode(b"Plain text message").decode("utf-8")
    html_data = base64.urlsafe_b64encode(b"<p>HTML message</p>").decode("utf-8")
    payload = {
        "mimeType": "multipart/alternative",
        "parts": [
            {
                "mimeType": "text/html",
                "body": {"data": html_data},
            },
            {
                "mimeType": "text/plain",
                "body": {"data": plain_data},
            },
        ],
    }
    body = gmail_service._extract_body(payload)
    # text/plain takes priority
    assert body == "Plain text message"


@pytest.mark.asyncio
async def test_get_emails_success(gmail_service):
    db_mock = AsyncMock()
    user_id = 42

    # Mock user record with refresh token
    user_mock = MagicMock()
    user_mock.google_refresh_token = "valid_refresh_token"

    # Mock Gmail client resource build
    mock_service = MagicMock()

    # Mock search messages list
    mock_service.users().messages().list().execute.return_value = {
        "messages": [{"id": "msg123"}]
    }

    # Mock get message content
    plain_data = base64.urlsafe_b64encode(b"Hello user, here is your update.").decode(
        "utf-8"
    )
    mock_service.users().messages().get().execute.return_value = {
        "id": "msg123",
        "snippet": "Hello user...",
        "payload": {
            "mimeType": "text/plain",
            "body": {"data": plain_data},
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "Subject", "value": "Test Subject"},
                {"name": "Date", "value": "Mon, 12 Jul 2026 12:00:00 UTC"},
            ],
        },
    }

    with patch.object(
        gmail_service, "_get_gmail_client", AsyncMock(return_value=mock_service)
    ):
        with patch(
            "app.services.gmail_service.crud_user.get",
            AsyncMock(return_value=user_mock),
        ):
            emails = await gmail_service.get_emails(user_id=user_id, db=db_mock)

            assert len(emails) == 1
            email = emails[0]
            assert email.id == "msg123"
            assert email.sender == "sender@example.com"
            assert email.subject == "Test Subject"
            assert email.body == "Hello user, here is your update."


@pytest.mark.asyncio
async def test_get_emails_truncation(gmail_service):
    db_mock = AsyncMock()
    user_id = 42

    user_mock = MagicMock()
    user_mock.google_refresh_token = "valid_refresh_token"

    mock_service = MagicMock()
    mock_service.users().messages().list().execute.return_value = {
        "messages": [{"id": "msg123"}]
    }

    # Body longer than 1500 chars (truncate length default is 1500)
    long_body = b"A" * 2000
    plain_data = base64.urlsafe_b64encode(long_body).decode("utf-8")
    mock_service.users().messages().get().execute.return_value = {
        "id": "msg123",
        "snippet": "Hello user...",
        "payload": {
            "mimeType": "text/plain",
            "body": {"data": plain_data},
            "headers": [],
        },
    }

    with patch.object(
        gmail_service, "_get_gmail_client", AsyncMock(return_value=mock_service)
    ):
        with patch(
            "app.services.gmail_service.crud_user.get",
            AsyncMock(return_value=user_mock),
        ):
            emails = await gmail_service.get_emails(user_id=user_id, db=db_mock)

            assert len(emails) == 1
            email = emails[0]
            assert len(email.body) == 1500 + len("\n... [truncated]")
            assert email.body.endswith("\n... [truncated]")


@pytest.mark.asyncio
async def test_get_emails_fallback_to_snippet(gmail_service):
    db_mock = AsyncMock()
    user_id = 42

    user_mock = MagicMock()
    user_mock.google_refresh_token = "valid_refresh_token"

    mock_service = MagicMock()
    mock_service.users().messages().list().execute.return_value = {
        "messages": [{"id": "msg123"}]
    }

    # Empty payload body
    mock_service.users().messages().get().execute.return_value = {
        "id": "msg123",
        "snippet": "Fallback Snippet Here",
        "payload": {"mimeType": "text/plain", "body": {"data": ""}, "headers": []},
    }

    with patch.object(
        gmail_service, "_get_gmail_client", AsyncMock(return_value=mock_service)
    ):
        with patch(
            "app.services.gmail_service.crud_user.get",
            AsyncMock(return_value=user_mock),
        ):
            emails = await gmail_service.get_emails(user_id=user_id, db=db_mock)

            assert len(emails) == 1
            email = emails[0]
            assert email.body == "Fallback Snippet Here"


@pytest.mark.asyncio
async def test_get_email_by_id_success(gmail_service):
    db_mock = AsyncMock()
    user_id = 42

    mock_service = MagicMock()
    plain_data = base64.urlsafe_b64encode(b"Single message body").decode("utf-8")
    mock_service.users().messages().get().execute.return_value = {
        "id": "msg999",
        "snippet": "Snippet text",
        "payload": {
            "mimeType": "text/plain",
            "body": {"data": plain_data},
            "headers": [
                {"name": "From", "value": "another@sender.com"},
                {"name": "Subject", "value": "Single Subject"},
                {"name": "Date", "value": "Mon, 12 Jul 2026 15:00:00 UTC"},
            ],
        },
    }

    with patch.object(
        gmail_service, "_get_gmail_client", AsyncMock(return_value=mock_service)
    ):
        email = await gmail_service.get_email_by_id(
            user_id=user_id, db=db_mock, message_id="msg999"
        )

        assert email.id == "msg999"
        assert email.sender == "another@sender.com"
        assert email.subject == "Single Subject"
        assert email.body == "Single message body"


@pytest.mark.asyncio
async def test_get_emails_refresh_error(gmail_service):
    db_mock = AsyncMock()
    user_id = 42

    with patch.object(
        gmail_service,
        "_get_gmail_client",
        AsyncMock(side_effect=RefreshError("Token expired")),
    ):
        with pytest.raises(RefreshError):
            await gmail_service.get_emails(user_id=user_id, db=db_mock)
