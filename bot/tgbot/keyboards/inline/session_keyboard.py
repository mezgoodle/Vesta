from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.keyboards.inline.callbacks.sessions import SessionCallbackFactory

MAX_TITLE_LENGTH = 24


def create_markup(session_id: int, session_title: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="✏️ Change session title",
            callback_data=SessionCallbackFactory(
                session_id=session_id, session_title=session_title, action="change"
            ).pack(),
        ),
        InlineKeyboardButton(
            text="❌ Delete session",
            callback_data=SessionCallbackFactory(
                session_id=session_id, session_title=session_title, action="delete"
            ).pack(),
        ),
    )
    builder.adjust(2)
    markup = builder.as_markup()
    return markup
