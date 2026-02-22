from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from tgbot.keyboards.inline.callbacks.user_edit import UserEditCallbackFactory


def edit_user_markup() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✔️ Edit",
                    callback_data=UserEditCallbackFactory(edit=True).pack(),
                ),
                InlineKeyboardButton(
                    text="❌ Cancel",
                    callback_data=UserEditCallbackFactory(edit=False).pack(),
                ),
            ]
        ],
    )
    return markup
