import asyncio
import logging

from app.core.config import settings
from app.crud.crud_user import user as crud_user
from app.db.session import AsyncSessionLocal
from app.schemas.user import UserCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_superuser():
    async with AsyncSessionLocal() as db:
        email = settings.SUPERUSER_EMAIL
        password = settings.SUPERUSER_PASSWORD

        user = await crud_user.get_by_email(db, email=email)
        if user:
            logger.info("User already exists.")
            return

        user_in = UserCreate(
            telegram_id=0,
            email=email,
            password=password,
            full_name="System Admin",
            username="admin",
            is_allowed=True,
            is_superuser=True,
        )

        user = await crud_user.create(db, obj_in=user_in)

        await db.commit()

        logger.info(f"Superuser {email} created successfully!")


if __name__ == "__main__":
    asyncio.run(create_superuser())
