from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loader import dp

from tgbot.filters.admin import IsAdminFilter
from tgbot.infrastructure.user_service import user_service
from tgbot.keyboards.inline.callbacks.permissions import PermissionsCallbackFactory
from tgbot.keyboards.inline.callbacks.user_edit import UserEditCallbackFactory
from tgbot.keyboards.inline.edit_user_keyboard import edit_user_markup
from tgbot.services.user_cache import UserCache
from tgbot.states.states import UserUpdateInfo

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


@router.callback_query(UserEditCallbackFactory.filter(F.edit))
async def edit_handler(
    callback: CallbackQuery,
    callback_data: UserEditCallbackFactory,
    state: FSMContext,
) -> Message:
    await state.set_state(UserUpdateInfo.email)
    return await callback.message.answer("Please enter user's email")


@router.message(UserUpdateInfo.email)
async def email_handler(message: Message, state: FSMContext) -> Message:
    await state.update_data(email=message.text)
    await state.set_state(UserUpdateInfo.password)
    return await message.answer("Please enter user's password")


@router.message(UserUpdateInfo.password)
async def password_handler(message: Message, state: FSMContext) -> Message:
    await state.update_data(password=message.text)
    await state.set_state(UserUpdateInfo.city_name)
    return await message.answer("Please enter user's city name")


@router.message(UserUpdateInfo.city_name)
async def city_name_handler(message: Message, state: FSMContext) -> Message:
    await state.update_data(city_name=message.text)
    data = await state.get_data()
    user_id = data.get("user_id")
    email = data.get("email")
    password = data.get("password")
    city_name = data.get("city_name")
    await state.clear()
    success, result = await user_service.update_user(
        user_id=user_id,
        email=email,
        password=password,
        city_name=city_name,
    )
    if success:
        return await message.answer(result)
    else:
        return await message.answer(result)
