from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault


async def set_default_commands(bot: Bot) -> None:
    """
    Set default bot commands for all users.

    Args:
        bot: The aiogram Bot instance
    """
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="help", description="Show help"),
        BotCommand(command="new", description="Start a new session"),
        BotCommand(command="chats", description="Show chat sessions"),
        BotCommand(command="reset", description="Reset current session"),
        BotCommand(command="today", description="Show today's events"),
        BotCommand(command="upcoming", description="Show upcoming events"),
        BotCommand(command="info", description="Show user info"),
    ]
    await bot.set_my_commands(commands=commands, scope=BotCommandScopeDefault())
