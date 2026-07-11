"""
Weather sub-agent — handles weather and forecast queries.
"""

from typing import Callable

from google.adk.agents import LlmAgent


def create_weather_agent(
    tools: list[Callable], model: str, current_time_str: str | None = None
) -> LlmAgent:
    """Create the Weather sub-agent."""
    instruction = (
        "You are a weather assistant within the Vesta smart assistant.\n"
        "Your responsibilities:\n"
        "1. Fetch weather information for any city using the get_weather_info tool.\n"
        "2. If the user's weather request is ambiguous, default to Ukraine.\n"
        "3. For requests about today, use days=1 whenever appropriate.\n"
        "Always respond in a friendly, concise manner."
    )
    if current_time_str:
        instruction = (
            f"Current Date and Time: {current_time_str}.\n"
            f"When resolving relative dates like 'today', 'tomorrow', 'this weekend', or 'next Monday', "
            f"use the 'Current Date' above as your reference.\n"
            f"{instruction}"
        )

    return LlmAgent(
        name="WeatherAgent",
        model=model,
        description=(
            "Handles weather and forecast requests. Delegate to this agent when "
            "the user asks about current weather, temperature, rain, forecast, "
            "or weather conditions in any city."
        ),
        instruction=instruction,
        tools=tools,
        mode="single_turn",
    )

