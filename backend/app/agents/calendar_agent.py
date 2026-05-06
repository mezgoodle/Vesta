"""
Calendar sub-agent — handles scheduling and calendar queries.
"""

from typing import Callable

from google.adk.agents import LlmAgent


def create_calendar_agent(tools: list[Callable], model: str) -> LlmAgent:
    """Create the Calendar sub-agent."""
    return LlmAgent(
        name="CalendarAgent",
        model=model,
        description=(
            "Handles scheduling and calendar event management. Delegate to this "
            "agent when the user asks about their schedule, wants to see upcoming "
            "events, or wants to create a calendar event."
        ),
        instruction=(
            "You are a scheduling assistant within the Vesta smart assistant.\n"
            "Your responsibilities:\n"
            "1. Retrieve upcoming calendar events using the get_calendar_events tool.\n"
            "2. Schedule new calendar events using the schedule_event_tool.\n"
            "3. For requests about 'today' or 'my day', call get_calendar_events(days=1).\n"
            "Always respond in a friendly, concise manner."
        ),
        tools=tools,
    )
