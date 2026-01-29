"""
Tool definitions for Gemini Function Calling.

These functions serve as declarations for the LLM to understand available tools.
The actual implementation logic is executed in LLMService._execute_function().
"""


def get_current_weather(city: str) -> dict:
    """
    Get the current weather information for a specified city.

    Args:
        city: The name of the city to get weather for (e.g., "London", "New York")

    Returns:
        A dictionary containing weather information including temperature,
        description, humidity, and wind speed.
    """
    pass


def get_calendar_events(days: int = 7) -> dict:
    """
    Get upcoming calendar events for the authenticated user.

    Args:
        days: Number of days to look ahead for events (default: 7)

    Returns:
        A dictionary containing a list of calendar events and the total count.
        Each event includes summary, start_time, end_time, location, and description.
    """
    pass
