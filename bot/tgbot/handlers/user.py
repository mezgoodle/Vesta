from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.markdown import hlink
from loader import dp

from tgbot.filters.approved_user import IsApprovedUserFilter
from tgbot.infrastructure.user_service import user_service
from tgbot.services.user_cache import UserCache
from tgbot.services.utils import format_user_data

router = Router()
dp.include_router(router)


@router.message(Command("info"))
async def user_info(message: Message) -> Message:
    user = await user_service.get_user_by_telegram_id(message.from_user.id)
    if user:
        await message.reply(format_user_data(user))
    else:
        await message.reply("You are not registered yet.")
    return


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


@router.message(Command("enable_daily_summary"), IsApprovedUserFilter())
async def enable_daily_summary(message: Message, user_db_id: int) -> Message:
    _, response_text = await user_service.enable_daily_summary(user_db_id)
    return await message.reply(response_text)
