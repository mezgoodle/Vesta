from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.markdown import hbold, hitalic
from loader import dp

router = Router()
dp.include_router(router)


@router.message(Command("help"))
async def help_command(message: Message) -> Message:
    text = f"""
    Hello, {hbold(message.from_user.username)}!
    If you are new here, you can start by typing /start or /help.
    Also you need to be approved by admin({hbold("@sylvenis")}) to use this bot.

    {hbold("User info:")}
    - To get your info, type /info

    {hbold("Conversation with AI:")}
    - To start conversation, type /new
    - To get list of conversations, type /chats
    - To reset the current conversation, type /reset

    {hbold("Weather:")}
    - To get weather in a city, type /weather {hitalic("city")}

    {hbold("News:")}
    - To get news, type /news {hitalic("category")}

    {hbold("Calendar:")}
    - To get today's events, type /today
    - To get upcoming events, type /upcoming or /upcoming {hitalic("days")}
    """
    await message.reply(text)
