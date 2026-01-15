from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.keyboards.inline.callbacks.sessions import SessionCallbackFactory

MAX_TITLE_LENGTH = 24


def truncate_to_bytes(text: str, max_bytes: int) -> str:
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
    return truncated.rstrip() + "..."


def create_markup(sessions: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for session in sessions:
        session_id = session.get("id")
        if not session_id:
            continue
        session_title = session.get("title", "Untitled")
        session_title = truncate_to_bytes(session_title, MAX_TITLE_LENGTH)
        builder.add(
            InlineKeyboardButton(
                text=session_title,
                callback_data=SessionCallbackFactory(
                    session_id=session_id, session_title=session_title
                ).pack(),
            )
        )
    builder.adjust(2)
    markup = builder.as_markup()
    return markup
