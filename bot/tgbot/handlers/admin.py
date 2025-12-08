from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from loader import dp

from tgbot.filters.admin import IsAdminFilter
from tgbot.infrastructure.user_service import user_service
from tgbot.keyboards.inline.callbacks.permissions import PermissionsCallbackFactory
from tgbot.services.user_cache import UserCache

router = Router()
router.message.filter(IsAdminFilter())
dp.include_router(router)


@router.message(Command("admin"))
async def command_admin_handler(message: Message) -> None:
    return await message.answer("You are admin!")


@router.callback_query(PermissionsCallbackFactory.filter(F.verdict == "approve"))
async def approve_handler(
    callback: CallbackQuery,
    callback_data: PermissionsCallbackFactory,
    user_cache: UserCache,
) -> None:
    # result = await user_service.update_user_approval(
    #     callback_data.user_id, {"is_allowed": True}
    # )
    result = "✅ User approved!"
    user_cache.add(callback_data.user_id)
    await callback.message.edit_text(result)
    try:
        await callback.bot.send_message(callback_data.user_id, "You are approved!")
    except Exception:
        pass
    await callback.answer()


@router.callback_query(PermissionsCallbackFactory.filter(F.verdict == "decline"))
async def decline_handler(
    callback: CallbackQuery,
    callback_data: PermissionsCallbackFactory,
) -> None:
    await callback.message.delete()
    try:
        await callback.bot.send_message(callback_data.user_id, "You are declined!")
    except Exception:
        pass
    await callback.answer()
