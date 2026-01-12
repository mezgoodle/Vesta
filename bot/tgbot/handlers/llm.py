from aiogram import Router
from aiogram.filters import Command, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loader import dp

from tgbot.config import Settings
from tgbot.infrastructure.llm_service import llm_service
from tgbot.keyboards.inline import sessions_keyboard
from tgbot.keyboards.inline.callbacks.sessions import SessionCallbackFactory
from tgbot.services.user_cache import UserCache

router = Router()
dp.include_router(router)


@router.message(Command("chats"))
async def get_chats_command(message: Message, user_cache: UserCache, config: Settings):
    sessions = await llm_service.get_sessions_by_user_id(
        user_cache.get_user_id_in_db(message.from_user.id)
    )
    if not sessions:
        return await message.answer("You have no sessions")
    markup = sessions_keyboard.create_markup(sessions)
    return await message.answer("Select a session", reply_markup=markup)


@router.callback_query(SessionCallbackFactory.filter())
async def approve_handler(
    callback: CallbackQuery,
    callback_data: SessionCallbackFactory,
    user_cache: UserCache,
    state: FSMContext,
) -> None:
    await state.update_data(session_id=callback_data.session_id)
    await callback.message.answer("Your session is selected. Send your message.")
    await callback.answer()
