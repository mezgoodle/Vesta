from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from loader import dp

from tgbot.filters.approved_user import IsApprovedUserFilter
from tgbot.infrastructure.calendar_service import calendar_service

router = Router()
router.message.filter(IsApprovedUserFilter())
dp.include_router(router)


@router.message(Command("today"))
async def today_command(message: Message, user_db_id: int):
    events = await calendar_service.get_today_events(user_db_id)
    return await message.answer(events)


@router.message(Command("upcoming"))
async def upcoming_command(message: Message, user_db_id: int, command: CommandObject):
    days = None
    command_args = command.args
    if not command_args:
        days = 7
    else:
        args = command.args.split()
        if len(args) != 1:
            return await message.answer("Please provide a valid number of days.")
        try:
            days = int(args[0])
        except ValueError:
            return await message.answer("Please provide a valid number of days.")
        if days <= 0:
            return await message.answer("Please provide a positive number of days.")
    events = await calendar_service.get_upcoming_events(user_db_id, days)
    return await message.answer(events)
