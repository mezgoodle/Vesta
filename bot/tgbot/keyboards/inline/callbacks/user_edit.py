from aiogram.filters.callback_data import CallbackData


class UserEditCallbackFactory(CallbackData, prefix="user_edit"):
    edit: bool
