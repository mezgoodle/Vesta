from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.markdown import hbold
from loader import dp

from tgbot.filters.approved_user import IsApprovedUserFilter
from tgbot.infrastructure.llm_service import llm_service
from tgbot.keyboards.inline import session_keyboard, sessions_keyboard
from tgbot.keyboards.inline.callbacks.sessions import SessionCallbackFactory
from tgbot.services.utils import format_sessions_message
from tgbot.states.states import ChatMessage, SessionUpdateInfo

router = Router()
router.message.filter(IsApprovedUserFilter())
dp.include_router(router)


@router.message(Command("chats"))
async def get_chats_command(message: Message, user_db_id: int):
    sessions = await llm_service.get_sessions_by_user_id(user_db_id)
    if not sessions:
        return await message.answer("You have no sessions")
    markup = sessions_keyboard.create_markup(sessions)
    formatted_sessions_message = format_sessions_message(sessions)
    return await message.answer(formatted_sessions_message, reply_markup=markup)


@router.callback_query(SessionCallbackFactory.filter(F.action == "change"))
async def session_change_handler(
    callback: CallbackQuery,
    callback_data: SessionCallbackFactory,
    state: FSMContext,
) -> None:
    await state.set_state(SessionUpdateInfo.session_title)
    await callback.message.answer("Enter new session title")
    await callback.answer()
    return


@router.callback_query(SessionCallbackFactory.filter(F.action == "delete"))
async def session_delete_handler(
    callback: CallbackQuery,
    callback_data: SessionCallbackFactory,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    result = await llm_service.delete_session(session_id=data.get("session_id"))
    if not result:
        return await callback.message.answer("Something went wrong")
    await state.clear()
    await callback.message.answer("Session deleted.")
    await callback.answer()
    return


@router.callback_query(SessionCallbackFactory.filter())
async def session_select_handler(
    callback: CallbackQuery,
    callback_data: SessionCallbackFactory,
    state: FSMContext,
) -> None:
    session_title = callback_data.session_title
    session_id = callback_data.session_id
    await state.update_data(
        session_id=session_id,
        session_title=session_title,
    )
    await state.set_state(ChatMessage.message)
    keyboard = session_keyboard.create_markup(session_id, session_title)
    await callback.message.edit_text(
        f"Your session is selected - {hbold(session_title)}. Send your message.\nTo edit session - use buttons below.",
        reply_markup=keyboard,
    )
    await callback.answer()
    return


@router.message(SessionUpdateInfo.session_title)
async def session_change_title_handler(message: Message, state: FSMContext):
    session_title = message.text
    data = await state.get_data()
    if not session_title:
        return await message.answer("Please enter a session title.")
    result = await llm_service.update_session(
        session_id=data.get("session_id"),
        data={"title": session_title},
    )
    if not result:
        return await message.answer("Something went wrong")
    await state.set_state(ChatMessage.message)
    return await message.answer("Session title changed. Send your message.")
