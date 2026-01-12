from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.keyboards.inline.callbacks.sessions import SessionCallbackFactory


def create_markup(sessions: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for session in sessions:
        builder.add(
            InlineKeyboardButton(
                text=session["title"],
                callback_data=SessionCallbackFactory(
                    session_id=session["id"], session_title=session["title"]
                ).pack(),
            )
        )
    builder.adjust(2)
    markup = builder.as_markup()
    return markup
