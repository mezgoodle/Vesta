from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.gmail import EmailMessage
from app.services.gemini_tools import create_tools


@pytest.fixture
def tools():
    db = AsyncMock()
    return create_tools(user_id=42, db=db), db


@pytest.mark.asyncio
async def test_check_emails_tool_success(tools):
    tool_groups, _ = tools
    email_tool = tool_groups["email"][0]  # check_emails

    with patch("app.services.gemini_tools.GmailService") as MockGmailService:
        mock_svc = MockGmailService.return_value
        mock_svc.get_emails = AsyncMock()

        email = EmailMessage(
            id="msg123",
            sender="boss@work.com",
            subject="Urgent Meeting",
            date="Today",
            snippet="We need to meet...",
            body="Full meeting details here.",
        )
        mock_svc.get_emails.return_value = [email]

        result = await email_tool(query="is:unread", max_results=5)

        assert "boss@work.com" in result
        assert "Urgent Meeting" in result
        assert "Full meeting details here" in result
        mock_svc.get_emails.assert_called_with(
            user_id=42,
            db=tools[1],
            query="is:unread",
            max_results=5,
        )


@pytest.mark.asyncio
async def test_check_emails_tool_empty(tools):
    tool_groups, _ = tools
    email_tool = tool_groups["email"][0]

    with patch("app.services.gemini_tools.GmailService") as MockGmailService:
        mock_svc = MockGmailService.return_value
        mock_svc.get_emails = AsyncMock(return_value=[])

        result = await email_tool(query="is:unread")
        assert "No emails found" in result


@pytest.mark.asyncio
async def test_check_emails_tool_error(tools):
    tool_groups, _ = tools
    email_tool = tool_groups["email"][0]

    with patch("app.services.gemini_tools.GmailService") as MockGmailService:
        mock_svc = MockGmailService.return_value
        mock_svc.get_emails = AsyncMock(side_effect=Exception("API limit"))

        result = await email_tool()
        assert "Unable to fetch emails" in result
