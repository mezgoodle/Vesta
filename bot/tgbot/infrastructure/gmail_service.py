from html import escape

from aiogram.utils.formatting import Bold, Underline
from aiogram.utils.markdown import hbold

from tgbot.infrastructure.base_service import BaseAPIService


class GmailService(BaseAPIService):
    """Service for Gmail operations on the Telegram bot side."""

    def __init__(self, base_url: str | None = None, timeout: int = 10):
        super().__init__(base_url, timeout)

    async def get_emails(
        self, user_id: int, query: str = "is:unread", max_results: int = 5
    ) -> str:
        """
        Fetch emails using a search query.

        Args:
            user_id: User ID to fetch emails for.
            query: Gmail search query.
            max_results: Max results to fetch.

        Returns:
            Formatted emails as a string.
        """
        endpoint = "/gmail/messages"
        params = {"user_id": user_id, "query": query, "max_results": max_results}

        status, data = await self._get(endpoint, params)

        if status == 200:
            return self._format_email_data(data, query)
        elif status == 401:
            return (
                "❌ Google OAuth authorization is required.\n"
                "Please run /google_auth to authorize access to your Gmail."
            )
        elif status == 403:
            return "❌ Google access expired. Please re-authorize via /google_auth."
        elif status == 404:
            return f"❌ No emails found matching search: <code>{escape(query)}</code>"
        else:
            return self._handle_error_response(
                status, data, f"fetching emails for query: {query}"
            )

    def _format_email_data(self, data: dict, query: str) -> str:
        """
        Format email data into a user-friendly message.
        """
        try:
            emails = data.get("emails", [])
            count = data.get("count", 0)

            if count == 0 or not emails:
                return (
                    f"📨 No emails found matching search: <code>{escape(query)}</code>"
                )

            header = f"📨 {hbold('Emails')} ({count} message{'s' if count != 1 else ''} matching <code>{escape(query)}</code>):\n\n"

            email_messages = []
            for idx, email in enumerate(emails, 1):
                sender = escape(email.get("sender", "Unknown Sender"))
                subject = email.get("subject", "No Subject")
                date = escape(email.get("date", "Unknown Date"))
                snippet = escape(email.get("snippet", ""))

                # Format event message
                email_msg = f"{hbold(idx)}. {Underline(Bold(subject)).as_html()}\n"
                email_msg += f"👤 {hbold('From:')} {sender}\n"
                email_msg += f"📅 {hbold('Date:')} {date}\n"
                if snippet:
                    email_msg += f"📝 {snippet}\n"

                email_messages.append(email_msg)

            return header + "\n".join(email_messages)

        except Exception:
            self.logger.error("Error formatting email data", exc_info=True)
            return "❌ Error formatting email messages."


gmail_service = GmailService()
