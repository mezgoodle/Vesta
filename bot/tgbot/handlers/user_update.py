from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loader import dp

from tgbot.filters.admin import IsAdminFilter
from tgbot.infrastructure.user_service import user_service
from tgbot.keyboards.inline.callbacks.user_edit import UserEditCallbackFactory
from tgbot.states.states import UserUpdateInfo

router = Router()
router.message.filter(IsAdminFilter())
dp.include_router(router)


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
