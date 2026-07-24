from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def create_markup() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Посилання на сайт",
                    url="https://mezgoodle.github.io/TelegramiaSite/telegramia/#manual",
                )
            ]
        ],
    )
    return markup
