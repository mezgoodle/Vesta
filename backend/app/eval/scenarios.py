import datetime
import re
from app.eval.models import EvalTestCase


def _validate_weather_args(args: dict) -> bool:
    """Validate that city argument is in English and non-empty."""
    city = args.get("city", "")
    if not city or not isinstance(city, str):
        return False
    # Check if city contains non-Latin characters (e.g. Cyrillic)
    has_cyrillic = bool(re.search(r"[\u0400-\u04FF]", city))
    return not has_cyrillic


def _validate_schedule_args(args: dict) -> bool:
    """Validate that schedule_event_tool receives required arguments and valid ISO date."""
    summary = args.get("summary", "")
    start_time_iso = args.get("start_time_iso", "")
    if not summary or not start_time_iso:
        return False
    try:
        datetime.datetime.fromisoformat(str(start_time_iso).replace("Z", "+00:00"))
        return True
    except (ValueError, TypeError):
        return False


def get_standard_eval_scenarios() -> list[EvalTestCase]:
    """Get the standard suite of evaluation test cases."""
    tomorrow_str = (
        datetime.datetime.now() + datetime.timedelta(days=1)
    ).strftime("%Y-%m-%d")

    return [
        EvalTestCase(
            name="direct_conversation",
            description="General conversation that should NOT trigger any tool calls.",
            prompt="Привіт! Як у тебе справи і що ти вмієш робити?",
            expected_tools=[],
            unexpected_tools=[
                "get_weather_info",
                "get_calendar_events",
                "schedule_event_tool",
            ],
        ),
        EvalTestCase(
            name="weather_single_tool",
            description="Weather lookup for Kyiv (requires English translation in tool args).",
            prompt="Яка зараз погода в Києві та який прогноз на найближчі дні?",
            expected_tools=["get_weather_info"],
            tool_arg_validators={"get_weather_info": _validate_weather_args},
        ),
        EvalTestCase(
            name="calendar_upcoming_events",
            description="User asking to check calendar schedule for this week.",
            prompt="Покажи мої заплановані події в календарі на цей тиждень.",
            expected_tools=["get_calendar_events"],
        ),
        EvalTestCase(
            name="tasks_listing",
            description="User asking to list pending tasks from Google Tasks.",
            prompt="Які у мене є невиконані завдання в списку справ?",
            expected_tools=["get_tasks_tool"],
        ),
        EvalTestCase(
            name="email_check_unread",
            description="User asking to check inbox emails.",
            prompt="Перевір мою пошту, чи є якісь важливі нові листи?",
            expected_tools=["check_emails"],
        ),
        EvalTestCase(
            name="calendar_schedule_event",
            description="Scheduling a meeting with specific time (requires ISO datetime formatting).",
            prompt=f"Заплануй зустріч 'Sync with Architecture Team' на {tomorrow_str} о 14:30 тривалістю 45 хвилин.",
            expected_tools=["schedule_event_tool"],
            tool_arg_validators={"schedule_event_tool": _validate_schedule_args},
        ),
        EvalTestCase(
            name="proactive_daily_briefing",
            description="Asking about 'today' / 'my day' which should proactively trigger calendar and weather.",
            prompt="Доброго ранку! Розкажи, що в мене на сьогодні заплановано і яка погода на вулиці?",
            expected_tools=["get_calendar_events", "get_weather_info"],
        ),
        EvalTestCase(
            name="remember_user_fact",
            description="User sharing a personal preference that should be stored in memory.",
            prompt="Запам'ятай, будь ласка: я п'ю тільки еспресо без цукру.",
            expected_tools=["remember_user_fact"],
        ),
    ]
