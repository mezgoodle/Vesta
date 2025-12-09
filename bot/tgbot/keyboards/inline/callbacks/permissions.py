from typing import Literal

from aiogram.filters.callback_data import CallbackData


class PermissionsCallbackFactory(CallbackData, prefix="permissions"):
    verdict: Literal["approve", "decline"]
    user_id: int
