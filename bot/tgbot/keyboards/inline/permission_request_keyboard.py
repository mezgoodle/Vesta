from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, User

from tgbot.keyboards.inline.callbacks.permissions import PermissionsCallbackFactory


def permissions_markup(user_id: int, user: User) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Approve",
                    callback_data=PermissionsCallbackFactory(
                        verdict="approve",
                        user_id=user_id,
                        full_name=user.full_name,
                        username=user.username,
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text="Decline",
                    callback_data=PermissionsCallbackFactory(
                        verdict="decline",
                        user_id=user_id,
                        full_name=user.full_name,
                        username=user.username,
                    ).pack(),
                ),
            ]
        ],
    )
    return markup
