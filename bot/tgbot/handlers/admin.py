from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loader import dp

from tgbot.filters.admin import IsAdminFilter
from tgbot.infrastructure.user_service import user_service
from tgbot.keyboards.inline.callbacks.permissions import PermissionsCallbackFactory
from tgbot.keyboards.inline.edit_user_keyboard import edit_user_markup
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
    state: FSMContext,
) -> None:
    success, result = await user_service.update_user_approval(
        user_id=callback_data.user_id,
        permissions={"is_allowed": True},
        full_name=callback_data.full_name,
        username=callback_data.username,
    )
    if success:
        user_cache.add(success["id"], callback_data.user_id)
        keyboard = edit_user_markup(callback_data.user_id)
        await state.update_data(user_id=success["id"])
        await callback.message.edit_text(result, reply_markup=keyboard)
        try:
            await callback.bot.send_message(callback_data.user_id, "You are approved!")
        except Exception:
            pass
    else:
        await callback.message.edit_text(result)
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
