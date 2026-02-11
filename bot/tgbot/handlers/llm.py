from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.markdown import hbold
from loader import dp

from tgbot.config import Settings
from tgbot.filters.approved_user import IsApprovedUserFilter
from tgbot.infrastructure.llm_service import llm_service
from tgbot.keyboards.inline import sessions_keyboard
from tgbot.keyboards.inline.callbacks.sessions import SessionCallbackFactory
from tgbot.services.stt import GoogleSTTService
from tgbot.states.states import ChatMessage

router = Router()
router.message.filter(IsApprovedUserFilter())
dp.include_router(router)


@router.message(Command("chats"))
async def get_chats_command(message: Message, user_db_id: int, config: Settings):
    sessions = await llm_service.get_sessions_by_user_id(user_db_id)
    if not sessions:
        return await message.answer("You have no sessions")
    markup = sessions_keyboard.create_markup(sessions)
    return await message.answer("Select a session", reply_markup=markup)


@router.message(Command("reset"))
async def reset_state_handler(message: Message, state: FSMContext):
    await state.clear()
    return await message.answer("State reset!")


@router.callback_query(SessionCallbackFactory.filter())
async def session_select_handler(
    callback: CallbackQuery,
    callback_data: SessionCallbackFactory,
    state: FSMContext,
) -> None:
    await state.update_data(
        session_id=callback_data.session_id,
        session_title=callback_data.session_title,
    )
    await callback.message.answer("Your session is selected.")
    await callback.answer()


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


@router.message(F.voice)
async def voice_message_handler(message: Message, state: FSMContext):
    audio_file = message.voice
    if not audio_file:
        return await message.answer("Please send a voice message.")
    audio_bytes = await message.bot.download(audio_file)
    stt_service = GoogleSTTService()
    text = await stt_service.recognize(audio_bytes.getvalue())
    if not text:
        return await message.answer(
            "Could not recognize speech from the voice message."
        )
    return await message.answer(text)


@router.message(ChatMessage.message)
async def user_message_handler(message: Message, state: FSMContext, user_db_id: int):
    text = message.text
    if not text:
        return await message.answer("Please send a text message.")

    await state.update_data(message=text)
    data = await state.get_data()
    session_id = data.get("session_id")
    session_title = data.get("session_title")

    _ = await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

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
        f"Session: {hbold(session_title)}\n"
        f"Continue typing to chat, or /chats to switch sessions, /reset to end."
    )
