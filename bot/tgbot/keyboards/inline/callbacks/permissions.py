from aiogram.filters.callback_data import CallbackData


class PermissionsCallbackFactory(CallbackData, prefix="permissions"):
    verdict: str
    user_id: int
