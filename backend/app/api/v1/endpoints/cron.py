import logging
from typing import Any

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import KnowledgeServiceDep, SessionDep, verify_cron_secret
from app.core.config import settings
from app.models.device import SmartDevice
from app.models.user import User
from app.schemas.open_meteo import OpenMeteoResponse
from app.services.gmail_service import gmail_service_instance
from app.services.google_calendar import google_calendar_service_instance
from app.services.home import HomeAssistantService
from app.services.llm import LLMService
from app.services.open_meteo_service import open_meteo_service_instance

logger = logging.getLogger(__name__)

# Protect all routes in this router with the cron secret validation dependency
router = APIRouter(dependencies=[Depends(verify_cron_secret)])


async def send_daily_digests(db: AsyncSession) -> int:
    """
    Run daily morning digests for enabled users.

    Args:
        db: The database session.

    Returns:
        int: The number of successfully sent digests.
    """
    logger.info("🌅 Starting Daily Morning Digest...")
    service = LLMService()
    sent_count = 0

    stmt = select(User).where(
        User.is_daily_summary_enabled,
        User.google_refresh_token.isnot(None),
        User.telegram_id.isnot(None),
    )
    result = await db.execute(stmt)
    users = result.scalars().all()

    for user in users:
        try:
            try:
                events = await google_calendar_service_instance.get_today_events(
                    user.id, db
                )
            except Exception as e:
                logger.warning(
                    f"Failed to fetch calendar events for user {user.id}: {e}"
                )
                events = []

            weather: OpenMeteoResponse | None = None
            try:
                weather = await open_meteo_service_instance.get_weather(
                    city=user.city_name or "Kyiv", days=1
                )
            except Exception as e:
                logger.warning(f"Failed to fetch weather for user {user.id}: {e}")

            emails = None
            try:
                emails = await gmail_service_instance.get_emails(
                    user_id=user.id, db=db, query="newer_than:1d", max_results=5
                )
            except Exception as e:
                logger.warning(
                    f"Failed to fetch emails for daily digest for user {user.id}: {e}"
                )

            if events:
                events_text = "\n".join(
                    [
                        f"- {e.start_time.strftime('%H:%M') if e.start_time else 'All day'}: {e.summary}"
                        for e in events
                    ]
                )
            else:
                events_text = "Сьогодні немає запланованих подій у календарі."

            if weather:
                weather_text = (
                    f"Погода в місті {weather.city_name}: "
                    f"зараз {weather.current_temp}°C, {weather.current_conditions}."
                )
                if weather.daily_forecasts:
                    today = weather.daily_forecasts[0]
                    weather_text += (
                        f" Прогноз на сьогодні: макс {today.max_temp}°C, мін {today.min_temp}°C, "
                        f"ймовірність опадів {today.precipitation_prob_max}%."
                    )
            else:
                weather_text = "Не вдалося отримати дані про погоду."

            if emails is None:
                emails_text = "Не вдалося перевірити пошту."
            elif emails:
                emails_text = "Останні листи за добу:\n" + "\n".join(
                    [f"- від {e.sender}: {e.subject}" for e in emails]
                )
            else:
                emails_text = "За останню добу нових листів не було."

            prompt = (
                f"Ось мій розклад на сьогодні:\n{events_text}\n\n"
                f"{weather_text}\n\n"
                f"{emails_text}\n\n"
                "Напиши мені коротке, позитивне ранкове привітання та підсумок мого дня. "
                "Використовуй емодзі. Звертайся до мене на ім'я (якщо знаєш) або просто друже.\n\n"
                f"{settings.TELEGRAM_HTML_GUIDELINES}"
            )

            digest_text = await service.chat(prompt, [], user.id, db)
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
            sent_count += 1

        except Exception as e:
            logger.error(f"Failed to send digest to user {user.id}: {e}")

    return sent_count


@router.post("/morning-digest", response_model=dict[str, Any])
async def post_morning_digest(db: SessionDep) -> dict[str, Any]:
    """
    Endpoint called to send morning digests.
    """
    sent_count = await send_daily_digests(db)
    return {"status": "success", "sent_digests_count": sent_count}


@router.post("/check-power-status", response_model=dict[str, Any])
async def post_check_power_status(db: SessionDep) -> dict[str, Any]:
    """
    Endpoint called to check power status on all smart devices.
    """
    stmt = select(SmartDevice)
    result = await db.execute(stmt)
    devices = result.scalars().all()

    checked_devices = []
    home_service = HomeAssistantService()
    try:
        for device in devices:
            logger.info(
                f"Checking power status for device {device.name} "
                f"(entity_id: {device.entity_id}, room: {device.room})"
            )
            try:
                state_data = await home_service.get_state(device.entity_id)
                state_val = (state_data or {}).get("state", "unknown")
            except Exception:
                logger.exception(
                    f"Failed to fetch state for device {device.name} "
                    f"(entity_id: {device.entity_id})"
                )
                state_val = "unknown"
            checked_devices.append(
                {
                    "id": device.id,
                    "name": device.name,
                    "entity_id": device.entity_id,
                    "status": "online"
                    if state_val not in ("unavailable", "unknown")
                    else "offline",
                    "state": state_val,
                }
            )
    finally:
        await home_service.close()

    logger.info(f"Power status check completed for {len(checked_devices)} devices.")
    return {
        "status": "success",
        "checked_devices_count": len(checked_devices),
        "devices": checked_devices,
    }


@router.post("/sync-knowledge", response_model=dict[str, Any])
async def post_sync_knowledge(
    knowledge_service: KnowledgeServiceDep,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """
    Endpoint called to sync knowledge base with Google Drive in the background.
    """
    background_tasks.add_task(knowledge_service.sync_with_drive)
    return {
        "status": "success",
        "message": "Knowledge base sync started in background",
    }
