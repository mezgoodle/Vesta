from typing import Any, Dict

from aiogram.utils.markdown import hbold, hcode


def format_user_data(user_data: Dict[str, Any]) -> str:
    """
    Format user data for Telegram message using HTML parse mode.
    """
    full_name = user_data.get("full_name") or "Unknown"
    username = user_data.get("username")
    telegram_id = user_data.get("telegram_id")
    email = user_data.get("email") or "Not set"
    city = user_data.get("city_name") or "Not set"
    timezone = user_data.get("timezone") or "UTC"

    is_allowed = user_data.get("is_allowed", False)
    is_superuser = user_data.get("is_superuser", False)
    daily_summary = user_data.get("is_daily_summary_enabled", False)

    lines = [
        f"👤 {hbold('User Profile')}",
        "",
        f"🆔 {hbold('ID:')} {hcode(telegram_id)}",
        f"👤 {hbold('Name:')} {full_name}",
        f"🔗 {hbold('Username:')} {f'@{username}' if username else 'Not set'}",
        f"📧 {hbold('Email:')} {email}",
        f"🌍 {hbold('City:')} {city}",
        f"🕒 {hbold('Timezone:')} {timezone}",
        "",
        f"⚙️ {hbold('Settings & Permissions:')}",
        f"• {'✅' if is_allowed else '❌'} {hbold('Access Allowed')}",
        f"• {'✅' if is_superuser else '❌'} {hbold('Superuser')}",
        f"• {'✅' if daily_summary else '❌'} {hbold('Daily Summary')}",
    ]

    return "\n".join(lines)
