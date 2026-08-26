"""
Mock tools for E2E benchmarking and testing Gemini models.

These tools mirror the real tools from ``app.services.gemini_tools`` without
touching real APIs, DBs, Google Calendar, or Gmail.
"""

from collections.abc import Callable


def create_mock_tools(
    on_tool_call: Callable[[str, dict], None] | None = None,
) -> list[Callable]:
    """
    Create a list of mock tools matching the Vesta agent tool signatures.

    Args:
        on_tool_call: Optional callback invoked when any tool is executed.

    Returns:
        List of callable tool functions for Google GenAI / ADK.
    """

    def _record(name: str, args: dict):
        if on_tool_call:
            on_tool_call(name, args)

    async def get_weather_info(city: str, days: int = 7) -> str:
        """
        Get the current weather and forecast for a specific city for up to 14 days. Use this for ANY weather-related questions.

        CRITICAL: ALWAYS translate the city name to English before calling this tool (e.g., 'Київ' -> 'Kyiv', 'Львів' -> 'Lviv'). Open-Meteo geocoding fails with Cyrillic.

        Args:
            city: The name of the city IN ENGLISH to get weather for (e.g., 'London', 'New York', 'Tokyo', 'Kyiv').
            days: Number of days to look ahead for forecast. Default is 7 days, up to 14 days.

        Returns:
            A formatted string with current weather and daily forecast.
        """
        _record("get_weather_info", {"city": city, "days": days})
        return (
            f"Current weather in {city}: 18.5°C (Condition Code: 1 - Mainly Clear)\n"
            f"Forecast:\n"
            f"- 2026-08-24: Max 22.0°C, Min 14.0°C, Precip Prob: 10%\n"
            f"- 2026-08-25: Max 24.0°C, Min 15.0°C, Precip Prob: 5%"
        )

    async def get_calendar_events(days: int = 7) -> str:
        """
        Get upcoming calendar events for the authenticated user.

        Use this function when the user asks about their schedule, meetings,
        appointments, or what's on their calendar.

        Args:
            days: Number of days to look ahead for events. Default is 7 days.
                 Use 1 for today, 7 for this week, 30 for this month.

        Returns:
            A formatted string listing upcoming calendar events with their titles,
            event IDs [ID: ...], start times, end times, and locations (if available).
        """
        _record("get_calendar_events", {"days": days})
        return (
            f"Upcoming events (next {days} days):\n"
            "1. Team Standup [ID: mock_event_1] - 2026-08-24 10:00 at Google Meet (Daily sync)\n"
            "2. Project Review [ID: mock_event_2] - 2026-08-24 14:00 at Office Room 3"
        )

    async def schedule_event_tool(
        summary: str,
        start_time_iso: str,
        duration_minutes: int = 60,
        description: str = "",
    ) -> str:
        """
        Schedule a new event in the user's Google Calendar.

        Use this function when the user wants to create, schedule, or add an event
        to their calendar. This includes meetings, appointments, reminders, or any
        time-blocked activity.

        IMPORTANT: The start_time_iso parameter MUST include both date and time in
        ISO 8601 format. Examples:
        - '2026-02-15T14:00:00' (February 15, 2026 at 2:00 PM)
        - '2026-03-01T09:30:00' (March 1, 2026 at 9:30 AM)

        The time will be interpreted in Europe/Kyiv timezone.

        Args:
            summary: The title/name of the event (e.g., 'Team Meeting', 'Doctor Appointment')
            start_time_iso: Start date and time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS).
                           MUST include both date and time components.
            duration_minutes: Duration of the event in minutes. Default is 60 minutes (1 hour).
            description: Optional description or notes for the event

        Returns:
            A success message with a link to the created event in Google Calendar.
        """
        _record(
            "schedule_event_tool",
            {
                "summary": summary,
                "start_time_iso": start_time_iso,
                "duration_minutes": duration_minutes,
                "description": description,
            },
        )
        return (
            f"✅ Event '{summary}' successfully created!\n"
            f"📅 {start_time_iso} (Duration: {duration_minutes}m)\n"
            f"🔗 View event: https://calendar.google.com/event?eid=mock_event_new"
        )

    async def update_calendar_event_tool(
        event_id: str,
        summary: str = "",
        start_time_iso: str = "",
        duration_minutes: int = 0,
        description: str = "",
        location: str = "",
    ) -> str:
        """
        Update an existing event in the user's Google Calendar.

        Args:
            event_id: The unique Google Calendar event ID.
            summary: Optional new title for the event.
            start_time_iso: Optional new start date and time in ISO 8601 format.
            duration_minutes: Optional duration of event in minutes.
            description: Optional new description.
            location: Optional new location.

        Returns:
            A success message or an error message.
        """
        _record(
            "update_calendar_event_tool",
            {
                "event_id": event_id,
                "summary": summary,
                "start_time_iso": start_time_iso,
                "duration_minutes": duration_minutes,
                "description": description,
                "location": location,
            },
        )
        return f"✅ Event '{summary or 'Updated Event'}' [ID: {event_id}] successfully updated!"

    async def delete_calendar_event_tool(event_id: str) -> str:
        """
        Delete an existing event from the user's Google Calendar.

        Args:
            event_id: The unique Google Calendar event ID to delete.

        Returns:
            A confirmation string.
        """
        _record("delete_calendar_event_tool", {"event_id": event_id})
        return f"✅ Calendar event [ID: {event_id}] successfully deleted!"

    async def check_emails(query: str = "is:unread", max_results: int = 5) -> str:
        """
        Search, retrieve, and read the authenticated user's email messages using Gmail search.

        Args:
            query: Gmail search query string. Default is "is:unread".
            max_results: Maximum number of emails to retrieve (1 to 10). Default is 5.

        Returns:
            A formatted string containing matching emails.
        """
        _record("check_emails", {"query": query, "max_results": max_results})
        return (
            f"Emails matching query '{query}':\n"
            "--- Email 1 ---\n"
            "📧 From: alex@example.com\n"
            "📝 Subject: Architecture sync update\n"
            "📅 Date: 2026-08-24 08:30\n"
            "📌 Snippet: Here is the updated architecture diagram for review.\n"
            "💬 Body: Hi team, please review the latest PR before noon."
        )

    async def get_tasks_tool(show_completed: bool = False) -> str:
        """
        Get the user's tasks / to-do list items from Google Tasks.

        Args:
            show_completed: Whether to include completed tasks.

        Returns:
            A formatted string list of tasks.
        """
        _record("get_tasks_tool", {"show_completed": show_completed})
        return (
            "Your Tasks:\n"
            "- [ID: mock_task_1] [needsAction] Prepare release notes, due: 2026-08-24 17:00\n"
            "- [ID: mock_task_2] [needsAction] Review pull request #42"
        )

    async def create_task_tool(
        title: str, notes: str | None = None, due: str | None = None
    ) -> str:
        """
        Create a new task / to-do item in Google Tasks.

        Args:
            title: The title or summary of the task.
            notes: Optional detailed description or notes for the task.
            due: Optional due datetime in ISO format.

        Returns:
            A confirmation string with the created task details.
        """
        _record("create_task_tool", {"title": title, "notes": notes, "due": due})
        due_info = f", due: {due}" if due else ""
        return f"Task created successfully: '{title}' [ID: mock_task_new]{due_info}"

    async def complete_task_tool(task_id: str) -> str:
        """
        Mark a task as completed in Google Tasks.

        Args:
            task_id: The ID of the task to complete.

        Returns:
            A confirmation string.
        """
        _record("complete_task_tool", {"task_id": task_id})
        return f"Task [ID: {task_id}] marked as completed."

    async def delete_task_tool(task_id: str) -> str:
        """
        Delete a task from Google Tasks.

        Args:
            task_id: The ID of the task to delete.

        Returns:
            A confirmation string.
        """
        _record("delete_task_tool", {"task_id": task_id})
        return f"Task [ID: {task_id}] successfully deleted."

    async def consult_knowledge_base(query: str) -> str:
        """
        Search the personal knowledge base for information from stored documents.

        Args:
            query: A natural-language question to search the knowledge base with.

        Returns:
            A relevant answer synthesized from the stored documents.
        """
        _record("consult_knowledge_base", {"query": query})
        return f"Knowledge base search result for '{query}': User documentation mentions standard setup guidelines."

    async def remember_user_fact(fact_content: str, category: str | None = None) -> str:
        """
        Remember a new personal fact about the user.

        Args:
            fact_content: The fact to remember (e.g., 'Wife's name is Anna').
            category: Optional classification (e.g., 'preferences', 'relationships', 'health', 'bio').

        Returns:
            A success message confirming the fact has been saved.
        """
        _record(
            "remember_user_fact",
            {"fact_content": fact_content, "category": category},
        )
        return f"Saved fact: [ID: 99] {fact_content}"

    async def delete_user_fact(fact_id: int) -> str:
        """
        Delete a previously saved personal fact by its database ID.

        Args:
            fact_id: The database ID of the fact to delete (e.g., 15).

        Returns:
            A message confirming the fact was successfully deleted or not found.
        """
        _record("delete_user_fact", {"fact_id": fact_id})
        return f"Successfully deleted fact [ID: {fact_id}]"

    return [
        get_weather_info,
        get_calendar_events,
        schedule_event_tool,
        update_calendar_event_tool,
        delete_calendar_event_tool,
        check_emails,
        get_tasks_tool,
        create_task_tool,
        complete_task_tool,
        delete_task_tool,
        consult_knowledge_base,
        remember_user_fact,
        delete_user_fact,
    ]
