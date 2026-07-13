"""
Email sub-agent — handles searching and reading user emails.
"""

from typing import Callable

from google.adk.agents import LlmAgent


def create_email_agent(
    tools: list[Callable], model: str, current_time_str: str | None = None
) -> LlmAgent:
    """Create the Email sub-agent."""
    instruction = (
        "You are an email assistant (secretary) within the Vesta smart assistant.\n"
        "Your responsibilities:\n"
        "1. Search, retrieve, and read the user's email messages using the check_emails tool.\n"
        "2. Extract key points, identify important dates, amounts, and calls to action (Action Items) in the email messages.\n"
        "3. Provide concise, structured, and helpful summaries of user emails.\n"
        "Always respond in a friendly, professional, and concise manner."
    )
    if current_time_str:
        instruction = (
            f"Current Date and Time: {current_time_str}.\n"
            f"Use the 'Current Date' above as a reference when interpreting relative time queries about emails.\n"
            f"{instruction}"
        )

    return LlmAgent(
        name="EmailAgent",
        model=model,
        description=(
            "Handles searching, checking, reading, and summarizing the user's emails and inbox. "
            "Delegate to this agent when the user asks about emails, messages, or checking their inbox."
        ),
        instruction=instruction,
        tools=tools,
        mode="chat",
    )
