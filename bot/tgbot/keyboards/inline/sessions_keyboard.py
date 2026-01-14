from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.keyboards.inline.callbacks.sessions import SessionCallbackFactory

MAX_TITLE_LENGTH = 27


def create_markup(sessions: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for session in sessions:
        session_id = session.get("id")
        if not session_id:
            continue
        session_title = session["title"]
        session_title = (
            session_title[:MAX_TITLE_LENGTH] + "..."
            if len(session_title) > MAX_TITLE_LENGTH
            else session_title
        )
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
