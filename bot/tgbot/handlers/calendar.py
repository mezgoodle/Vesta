from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from loader import dp

from tgbot.filters.approved_user import IsApprovedUserFilter

router = Router()
router.message.filter(IsApprovedUserFilter())
dp.include_router(router)


@router.message(Command("calendar"))
async def command_calendar_handler(message: Message) -> None:
    return await message.answer("Calendar command!")
