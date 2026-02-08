from aiogram.dispatcher.filters import CommandHelp
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from loader import dp


@dp.message_handler(CommandHelp(), state="*")
async def help_command(message: Message) -> Message:
    text = f"""
    Hello, {hbold(message.from_user.username)}!
    If you are new here, you can start by typing "/start" or "/help".
    Also you need to be approved by admin({hbold("@sylvenis")}) to use this bot.

    {hbold("Conversation with AI:")}
    - To start conversation, type "/new"
    - To get list of conversations, type "/chats"
    - To reset the current conversation, type "/reset"

    {hbold("Weather:")}
    - To get weather in a city, type "/weather <city>"

    {hbold("News:")}
    - To get news, type "/news <category>"

    {hbold("Calendar:")}
    - To get calendar, type "/calendar"
    """
    await message.reply(text)
