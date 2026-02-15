import logging

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.schemas.weather import WeatherData
from app.services.google_calendar import google_calendar_service_instance
from app.services.llm import LLMService
from app.services.weather import weather_service_instance

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def send_daily_digests():
    logger.info("🌅 Starting Daily Morning Digest...")
    service = LLMService()

    async with AsyncSessionLocal() as db:
        stmt = select(User).where(
            User.is_daily_summary_enabled,
            User.google_refresh_token.isnot(None),
            User.telegram_id.isnot(None),
        )
        result = await db.execute(stmt)
        users = result.scalars().all()

        for user in users:
            try:
                events = await google_calendar_service_instance.get_today_events(
                    user.id, db
                )
                weather: WeatherData = (
                    await weather_service_instance.get_current_weather_by_city_name(
                        user.city_name or "Kyiv"
                    )
                )

                if not events:
                    continue

                events_text = "\n".join(
                    [
                        f"- {e.start_time.strftime('%H:%M') if e.start_time else 'All day'}: {e.summary}"
                        for e in events
                    ]
                )
                weather_text = f"Погода в місті {user.city_name}: {weather.temperature}°C, {weather.description}"

                prompt = (
                    f"Ось мій розклад на сьогодні:\n{events_text}\n\n"
                    f"{weather_text}\n\n"
                    "Напиши мені коротке, позитивне ранкове привітання та підсумок мого дня. "
                    "Використовуй емодзі. Звертайся до мене на ім'я (якщо знаєш) або просто друже."
                )

                digest_text = await service.chat(prompt, [])
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                        data={
                            "chat_id": user.telegram_id,
                            "text": digest_text,
                            "parse_mode": "HTML",
                        },
                    )
                    response.raise_for_status()

                logger.info(f"Digest sent to user {user.id}")

            except Exception as e:
                logger.error(f"Failed to send digest to user {user.id}: {e}")


def start_scheduler():
    logger.info("Starting scheduler...")
    scheduler.add_job(
        send_daily_digests, "cron", hour=8, minute=0, timezone="Europe/Kiev"
    )
    scheduler.start()
    logger.info("Scheduler started successfully")


def shutdown_scheduler():
    logger.info("Shutting down scheduler...")
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler shut down successfully")
    else:
        logger.info("Scheduler was not running")
