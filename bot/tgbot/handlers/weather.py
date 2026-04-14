from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from loader import dp

from tgbot.infrastructure.weather_service import weather_service

router = Router()
dp.include_router(router)


@router.message(Command("weather"))
async def weather_command(message: Message, command: CommandObject):
    if not command.args:
        await message.reply("❓ Please provide a city name.\nExample: /weather London")
        return

    args = command.args.split()
    
    days = 1
    last_arg = args[-1]
    
    try:
        days = int(last_arg)
        city_parts = args[:-1]
    except ValueError:
        city_parts = args
        
    if not city_parts:
        await message.reply("❓ Please provide a city name.\nExample: /weather London 3")
        return
        
    city_name = " ".join(city_parts)

    weather_info = await weather_service.get_forecast(city_name, days=days)

    return await message.answer(weather_info)
