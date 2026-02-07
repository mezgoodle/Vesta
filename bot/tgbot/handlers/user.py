from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.markdown import hlink
from loader import dp

from tgbot.infrastructure.user_service import user_service
from tgbot.services.user_cache import UserCache

router = Router()
dp.include_router(router)


@router.message(Command("google_auth"))
async def google_auth(message: Message, user_cache: UserCache) -> Message:
    data, _ = await user_service.start_google_auth(
        user_cache.get_user_id_in_db(message.from_user.id)
    )
    if data and (url := data.get("authorization_url")):
        await message.reply(
            f"Please visit the {hlink('URL', url)} to authorize access to your Google Calendar"
        )
    return
