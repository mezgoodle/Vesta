from aiogram.filters.callback_data import CallbackData


class SessionCallbackFactory(CallbackData, prefix="session"):
    session_id: int
    session_title: str
