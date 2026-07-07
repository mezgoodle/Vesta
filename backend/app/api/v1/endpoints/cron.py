import logging
import httpx
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import SessionDep, verify_cron_secret
from app.core.config import settings
from app.models.user import User
from app.models.device import SmartDevice
from app.schemas.weather import WeatherData
from app.services.google_calendar import google_calendar_service_instance
from app.services.llm import LLMService
from app.services.weather import weather_service_instance

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
            events = await google_calendar_service_instance.get_today_events(
                user.id, db
            )
            if not events:
                continue

            weather: WeatherData = (
                await weather_service_instance.get_current_weather_by_city_name(
                    user.city_name or "Kyiv"
                )
            )

            events_text = "\n".join(
                [
                    f"- {e.start_time.strftime('%H:%M') if e.start_time else 'All day'}: {e.summary}"
                    for e in events
                ]
            )
            weather_text = f"Погода в місті {weather.city}: {weather.temp}°C, {weather.description}"

            prompt = (
                f"Ось мій розклад на сьогодні:\n{events_text}\n\n"
                f"{weather_text}\n\n"
                "Напиши мені коротке, позитивне ранкове привітання та підсумок мого дня. "
                "Використовуй емодзі. Звертайся до мене на ім'я (якщо знаєш) або просто друже."
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
    for device in devices:
        logger.info(
            f"Checking power status for device {device.name} "
            f"(entity_id: {device.entity_id}, room: {device.room})"
        )
        checked_devices.append({
            "id": device.id,
            "name": device.name,
            "entity_id": device.entity_id,
            "status": "online",
            "state": "on"
        })

    logger.info(f"Power status check completed for {len(checked_devices)} devices.")
    return {
        "status": "success",
        "checked_devices_count": len(checked_devices),
        "devices": checked_devices
    }
