"""
Calendar sub-agent — handles scheduling and calendar queries.
"""

from typing import Callable

from google.adk.agents import LlmAgent


def create_calendar_agent(
    tools: list[Callable], model: str, current_time_str: str | None = None
) -> LlmAgent:
    """Create the Calendar sub-agent."""
    instruction = (
        "You are a scheduling assistant within the Vesta smart assistant.\n"
        "Your responsibilities:\n"
        "1. Retrieve upcoming calendar events using the get_calendar_events tool.\n"
        "2. Schedule new calendar events using the schedule_event_tool.\n"
        "3. For requests about 'today' or 'my day', call get_calendar_events(days=1).\n"
        "Always respond in a friendly, concise manner."
    )
    if current_time_str:
        instruction = (
            f"Current Date and Time: {current_time_str}.\n"
            f"When scheduling or retrieving events, use the 'Current Date' above as a reference "
            f"to calculate relative dates like 'today', 'tomorrow', 'yesterday', or 'next Friday'.\n"
            f"{instruction}"
        )

    return LlmAgent(
        name="CalendarAgent",
        model=model,
        description=(
            "Handles scheduling and calendar event management. Delegate to this "
            "agent when the user asks about their schedule, wants to see upcoming "
            "events, or wants to create a calendar event."
        ),
        instruction=instruction,
        tools=tools,
        mode="chat",
    )

