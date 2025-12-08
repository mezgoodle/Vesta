import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
from loader import bot, dp
from tgbot.config import Settings, config
from tgbot.middlewares.acl import ACLMiddleware
from tgbot.middlewares.settings import ConfigMiddleware
from tgbot.middlewares.throttling import ThrottlingMiddleware
from tgbot.services.admins_notify import on_startup_notify
from tgbot.services.setting_commands import set_default_commands
from tgbot.services.user_cache import UserCache


def register_all_handlers() -> None:
    from tgbot import handlers  # noqa: F401

    logging.info("Handlers registered.")


async def register_all_commands(bot: Bot) -> None:
    await set_default_commands(bot)
    logging.info("Commands registered.")


def register_global_middlewares(dp: Dispatcher, config: Settings):
    middlewares = [
        ConfigMiddleware(config),
        ThrottlingMiddleware(),
        ACLMiddleware(),
    ]

    for middleware in middlewares:
        dp.message.outer_middleware(middleware)
        dp.callback_query.outer_middleware(middleware)

    dp.callback_query.middleware(
        CallbackAnswerMiddleware(pre=True, text="Ready!", show_alert=True)
    )
    logging.info("Middlewares registered.")


async def on_startup(bot: Bot, dispatcher: Dispatcher) -> None:
    register_all_handlers()
    register_global_middlewares(dispatcher, config)
    await register_all_commands(bot)
    await on_startup_notify(bot)
    logging.info("Bot started.")


async def on_shutdown(dispatcher: Dispatcher) -> None:
    await dispatcher.storage.close()
    logging.info("Storage closed.")
    logging.info("Bot stopped.")


async def main() -> None:
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    user_cache = UserCache()
    fake_users_from_db = [111, 222]
    user_cache.load(fake_users_from_db)

    dp.workflow_data.update(user_cache=user_cache)

    # And the run events dispatching
    await dp.start_polling(bot)
    # * For the webhook usage:
    # * https://docs.aiogram.dev/en/dev-3.x/dispatcher/webhook.html#examples


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        filename="bot.log",
        format="%(asctime)s :: %(levelname)s :: %(module)s.%(funcName)s :: %(lineno)d :: %(message)s",  # noqa: E501
        filemode="w",
    )
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.warning("Bot stopped!")
