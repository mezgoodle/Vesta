from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from tgbot.keyboards.inline.callbacks.permissions import PermissionsCallbackFactory


def permissions_markup(user_id: int) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Approve",
                    callback_data=PermissionsCallbackFactory(
                        verdict="approve", user_id=user_id
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text="Decline",
                    callback_data=PermissionsCallbackFactory(
                        verdict="decline", user_id=user_id
                    ).pack(),
                ),
            ]
        ],
    )
    return markup
