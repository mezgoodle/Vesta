import asyncio
import logging

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.services.google_calendar import google_calendar_service_instance
from app.services.llm import LLMService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def send_daily_digests():
    logger.info("🌅 Starting Daily Morning Digest...")

    async with AsyncSessionLocal() as db:
        # 1. Знаходимо юзерів, які хочуть дайджест і мають токен
        stmt = select(User).where(
            User.is_daily_summary_enabled,
            User.google_refresh_token.isnot(None),
            User.telegram_id.isnot(None),
        )
        result = await db.execute(stmt)
        users = result.scalars().all()

        for user in users:
            try:
                # 2. Отримуємо події
                events = await google_calendar_service_instance.get_today_events(
                    user.id, db
                )

                if not events:
                    # Якщо подій немає - можна пропустити або побажати гарного дня
                    continue

                # 3. Формуємо текст для LLM
                # Перетворюємо об'єкти CalendarEvent у зрозумілий текст
                events_text = "\n".join(
                    [
                        f"- {e.start_time.strftime('%H:%M') if e.start_time else 'All day'}: {e.summary}"
                        for e in events
                    ]
                )

                prompt = (
                    f"Ось мій розклад на сьогодні:\n{events_text}\n\n"
                    "Напиши мені коротке, позитивне ранкове привітання та підсумок мого дня. "
                    "Використовуй емодзі. Звертайся до мене на ім'я (якщо знаєш) або просто друже."
                )

                # 4. Генеруємо текст через Gemini
                # (Тут важливо: ми не передаємо історію чату, це окремий запит)
                service = LLMService()
                digest_text = await service.chat(prompt, [])

                # 5. Відправляємо в Телеграм (прямий запит)
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                        data={
                            "chat_id": user.telegram_id,
                            "text": digest_text,
                            "parse_mode": "HTML",
                        },
                    )

                logger.info(f"Digest sent to user {user.id}")

            except Exception as e:
                logger.error(f"Failed to send digest to user {user.id}: {e}")


def setup_scheduler():
    # scheduler.add_job(
    #     send_daily_digests, "cron", hour=8, minute=0, timezone="Europe/Kiev"
    # )
    scheduler.add_job(send_daily_digests, "interval", seconds=10)
    scheduler.start()
