import asyncio
import logging
import os
import signal

from aiogram import Bot, Dispatcher
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    setup_application,
)
from aiohttp import web
from loader import bot, dp
from tgbot.config import Settings, config
from tgbot.infrastructure.logger import setup_logging
from tgbot.infrastructure.user_service import user_service
from tgbot.middlewares.logging import LoggingMiddleware
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
        LoggingMiddleware(),
        ConfigMiddleware(config),
        ThrottlingMiddleware(),
        # ACLMiddleware(),
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

    if not (config.DEBUG or not config.WEBHOOK_DOMAIN):
        webhook_url = config.WEBHOOK_DOMAIN.rstrip("/") + config.WEBHOOK_PATH
        secret_token = (
            config.WEBHOOK_SECRET.get_secret_value() if config.WEBHOOK_SECRET else None
        )
        await bot.set_webhook(url=webhook_url, secret_token=secret_token)
        logging.info(f"Webhook set to: {webhook_url}")

    await on_startup_notify(bot)
    logging.info("Bot started.")


async def on_shutdown(bot: Bot, dispatcher: Dispatcher) -> None:
    await dispatcher.storage.close()
    logging.info("Storage closed.")
    logging.info("Bot stopped.")


async def main() -> None:
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    user_cache = UserCache()

    # Retry cache initialization at startup until it successfully loads from the database
    users_from_db = None
    attempt = 1
    while users_from_db is None:
        logging.info(f"Fetching approved users from database (attempt {attempt})...")
        users_from_db = await user_service.get_approved_users()
        if users_from_db is None:
            logging.warning("Failed to fetch approved users. Retrying in 5 seconds...")
            await asyncio.sleep(5)
            attempt += 1

    user_cache.load(users_from_db)

    dp.workflow_data.update(user_cache=user_cache)

    if config.DEBUG or not config.WEBHOOK_DOMAIN:
        logging.info("Starting bot in Long Polling mode...")
        await dp.start_polling(bot)
    else:
        logging.info("Starting bot in Webhook mode...")

        if not config.WEBHOOK_SECRET:
            raise ValueError("WEBHOOK_SECRET must be set when running in Webhook mode.")

        port_env = os.getenv("PORT")
        port = int(port_env) if port_env else config.APP_PORT
        host = config.APP_HOST

        app = web.Application()

        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
            secret_token=config.WEBHOOK_SECRET.get_secret_value(),
        )
        webhook_requests_handler.register(app, path=config.WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=host, port=port)
        await site.start()
        logging.info(f"Webhook server running on {host}:{port}")

        stop_event = asyncio.Event()
        try:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass

        try:
            await stop_event.wait()
        finally:
            await runner.cleanup()


if __name__ == "__main__":
    # Setup logging (GCP or local based on DEBUG setting)
    setup_logging()

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.warning("Bot stopped!")
