from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from loader import dp

from tgbot.infrastructure.weather_service import weather_service

router = Router()
dp.include_router(router)


@router.message(Command("weather"))
async def weather_command(message: Message, command: CommandObject):
    args = command.args.split()

    if not args:
        await message.reply("❓ Please provide a city name.\nExample: /weather London")
        return

    if len(args) > 1:
        await message.reply("❓ Please provide a city name.\nExample: /weather London")
        return

    city_name = args[0].strip()

    weather_info = await weather_service.get_current_weather(city_name)

    return await message.answer(weather_info)
