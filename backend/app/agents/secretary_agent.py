"""
Secretary sub-agent — handles scheduling, calendar, and email/inbox queries.
"""

from typing import Callable

from google.adk.agents import LlmAgent


def create_secretary_agent(
    tools: list[Callable], model: str, current_time_str: str | None = None
) -> LlmAgent:
    """Create the Secretary sub-agent."""
    from app.core.config import settings

    instruction = (
        "You are a secretary assistant within the Vesta smart assistant.\n"
        "Your responsibilities:\n"
        "1. Retrieve upcoming calendar events using the get_calendar_events tool.\n"
        "2. Schedule new calendar events using the schedule_event_tool.\n"
        "3. Search, retrieve, and read the user's email messages using the check_emails tool.\n"
        "4. Extract key points, identify important dates, amounts, and calls to action (Action Items) in the email messages.\n"
        "5. Provide concise, structured, and helpful summaries of user emails.\n"
        "6. For requests about 'today' or 'my day', call get_calendar_events(days=1).\n"
        "Always respond in a friendly, professional, and concise manner.\n\n"
        f"{settings.TELEGRAM_HTML_GUIDELINES}"
    )
    if current_time_str:
        instruction = (
            f"Current Date and Time: {current_time_str}.\n"
            f"When scheduling or retrieving events/emails, use the 'Current Date' above as a reference "
            f"to calculate relative dates like 'today', 'tomorrow', 'yesterday', or 'next Friday'.\n"
            f"{instruction}"
        )

    return LlmAgent(
        name="SecretaryAgent",
        model=model,
        description=(
            "Handles scheduling, calendar management, and searching/reading user emails or inbox. "
            "Delegate to this agent when the user asks about their schedule, wants to see upcoming "
            "events, create a calendar event, check their email/inbox, or search for messages."
        ),
        instruction=instruction,
        tools=tools,
        mode="chat",
    )
