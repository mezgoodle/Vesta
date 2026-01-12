from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from loader import bot, dp

from tgbot.config import Settings
from tgbot.keyboards.inline.permission_request_keyboard import permissions_markup
from tgbot.services.user_cache import UserCache

router = Router()
dp.include_router(router)


@router.message(CommandStart())
async def command_start_handler(
    message: Message, user_cache: UserCache, config: Settings
) -> None:
    user_id = message.from_user.id

    if user_cache.is_allowed(user_id):
        return await message.answer(f"Hello, {hbold(message.from_user.full_name)}!")

    await message.answer(
        "You are not allowed to use this bot. Permission request has been sent to the administrator."
    )

    admin_id = config.admins[0]

    return await bot.send_message(
        chat_id=admin_id,
        text=f"👤 <b>New user!</b>\n"
        f"Name: {message.from_user.full_name}\n"
        f"ID: {user_id}\n"
        f"Username: @{message.from_user.username}",
        reply_markup=permissions_markup(user_id=user_id),
    )


@router.message(F.photo)
async def photo_msg(message: Message):
    await message.answer("This is image!")


@router.message()
async def echo_handler(message: Message, config: Settings) -> None:
    try:
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        await message.answer("Nice try!")


@router.message(Command("reset"))
async def reset_state_handler(message: Message, state: FSMContext):
    await state.clear()
    return await message.answer("State reset!")
