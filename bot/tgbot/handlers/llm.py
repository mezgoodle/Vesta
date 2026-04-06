import base64
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message
from aiogram.utils.markdown import hbold
from loader import dp

from tgbot.filters.approved_user import IsApprovedUserFilter
from tgbot.infrastructure.llm_service import llm_service
from tgbot.services.stt import stt_service
from tgbot.states.states import ChatMessage

router = Router()
router.message.filter(IsApprovedUserFilter())
dp.include_router(router)


@router.message(Command("reset"))
async def reset_state_handler(message: Message, state: FSMContext):
    await state.clear()
    return await message.answer("State reset!")


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
    return await _process_llm_request(message, state, user_db_id, text, want_voice=True)


@router.message(ChatMessage.message)
async def user_message_handler(message: Message, state: FSMContext, user_db_id: int):
    text = message.text
    if not text:
        return await message.answer("Please send a text message.")
    return await _process_llm_request(message, state, user_db_id, text)


async def _process_llm_request(
    message: Message, state: FSMContext, user_db_id: int, text: str, want_voice: bool = False
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
        want_voice=want_voice,
    )
    if not response:
        return await message.answer("Something went wrong")

    llm_response = response.get("response")
    if not llm_response:
        return await message.answer("Received an empty response from the assistant.")

    if audio_b64 := response.get("voice_audio"):
        voice_audio = base64.b64decode(audio_b64)
        voice = BufferedInputFile(voice_audio, filename="speech.ogg")
        await message.answer_voice(voice)

    await message.answer(llm_response)

    session_title = session_title or response.get("session_title")
    await state.update_data(session_title=session_title)
    await state.set_state(ChatMessage.message)
    return await message.answer(
        "Continue typing to chat, or /chats to switch sessions, /reset to end."
    )
