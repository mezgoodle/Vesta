"""
Secretary sub-agent — handles scheduling, calendar, and weather queries.

This module provides a factory function that creates an ``LlmAgent`` with
the calendar and weather tools already attached.  The factory pattern is
necessary because the tools are closures that capture request-scoped
``user_id`` and ``db`` references (see ``gemini_tools.create_tools``).
"""

from typing import Callable

from google.adk.agents import LlmAgent


def create_secretary_agent(tools: list[Callable], model: str) -> LlmAgent:
    """
    Create the Secretary sub-agent.

    Args:
        tools: Pre-bound tool functions for weather + calendar
               (``get_weather_info``, ``get_calendar_events``,
               ``schedule_event_tool``).
        model: The Gemini model name (e.g. ``gemini-2.5-flash``).

    Returns:
        A configured ``LlmAgent`` ready for use as a sub-agent.
    """
    return LlmAgent(
        name="SecretaryAgent",
        model=model,
        description=(
            "Handles scheduling, calendar events, and weather queries. "
            "Delegate to this agent when the user asks about their schedule, "
            "wants to create/view calendar events, or asks about the weather."
        ),
        instruction=(
            "You are a scheduling and weather assistant within the Vesta smart assistant.\n"
            "Your responsibilities:\n"
            "1. Fetch weather information for any city using the get_weather_info tool.\n"
            "2. Retrieve upcoming calendar events using the get_calendar_events tool.\n"
            "3. Schedule new calendar events using the schedule_event_tool.\n"
            "4. When the user asks about 'today' or 'my day', proactively call BOTH "
            "get_calendar_events(days=1) and get_weather_info(city='Kyiv', days=1) "
            "to provide a complete daily briefing.\n"
            "5. If the user's weather request is ambiguous, default to Ukraine.\n"
            "Always respond in a friendly, concise manner."
        ),
        tools=tools,
    )
