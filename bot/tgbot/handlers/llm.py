from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.markdown import hbold
from loader import dp

from tgbot.config import Settings
from tgbot.filters.approved_user import IsApprovedUserFilter
from tgbot.infrastructure.llm_service import llm_service
from tgbot.keyboards.inline import session_keyboard, sessions_keyboard
from tgbot.keyboards.inline.callbacks.sessions import SessionCallbackFactory
from tgbot.services.stt import stt_service
from tgbot.services.utils import format_sessions_message
from tgbot.states.states import ChatMessage, SessionUpdateInfo

router = Router()
router.message.filter(IsApprovedUserFilter())
dp.include_router(router)


@router.message(Command("chats"))
async def get_chats_command(message: Message, user_db_id: int, config: Settings):
    sessions = await llm_service.get_sessions_by_user_id(user_db_id)
    if not sessions:
        return await message.answer("You have no sessions")
    markup = sessions_keyboard.create_markup(sessions)
    formatted_sessions_message = format_sessions_message(sessions)
    return await message.answer(formatted_sessions_message, reply_markup=markup)


@router.message(Command("reset"))
async def reset_state_handler(message: Message, state: FSMContext):
    await state.clear()
    return await message.answer("State reset!")


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


@router.callback_query(SessionCallbackFactory.filter(F.action == "delete"))
async def session_delete_handler(
    callback: CallbackQuery,
    callback_data: SessionCallbackFactory,
    state: FSMContext,
) -> None:
    await callback.message.answer("Session deleted")
    return


@router.message(Command("new"))
async def new_message_command(message: Message, state: FSMContext):
    data = await state.get_data()
    if session_title := data.get("session_title"):
        await message.answer(
            f"You are in session {hbold(session_title)}. Send your message."
        )
    else:
        await message.answer("Send your message.")
        await message.answer(
            "You will start a new session. If you want to continue the conversation, type /chats."
        )
    await state.set_state(ChatMessage.message)


@router.message(ChatMessage.message, F.voice)
async def voice_message_handler(message: Message, state: FSMContext, user_db_id: int):
    audio_file = message.voice
    audio_bytes = await message.bot.download(audio_file)
    text = await stt_service.recognize(audio_bytes.getvalue())
    if not text:
        return await message.answer(
            "Could not recognize speech from the voice message."
        )
    return await _process_llm_request(message, state, user_db_id, text)


@router.message(ChatMessage.message)
async def user_message_handler(message: Message, state: FSMContext, user_db_id: int):
    text = message.text
    if not text:
        return await message.answer("Please send a text message.")
    return await _process_llm_request(message, state, user_db_id, text)


async def _process_llm_request(
    message: Message, state: FSMContext, user_db_id: int, text: str
):
    await state.update_data(message=text)
    data = await state.get_data()
    session_id = data.get("session_id")
    session_title = data.get("session_title")

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    response = await llm_service.process_prompt(
        prompt=text,
        user_id=user_db_id,
        session_id=session_id,
    )
    if not response:
        return await message.answer("Something went wrong")

    llm_response = response.get("response")
    if not llm_response:
        return await message.answer("Received an empty response from the assistant.")

    await message.answer(llm_response)

    session_title = session_title or response.get("session_title")
    await state.update_data(session_title=session_title)
    await state.set_state(ChatMessage.message)
    return await message.answer(
        "Continue typing to chat, or /chats to switch sessions, /reset to end."
    )
