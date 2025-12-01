from app.crud.base import CRUDBase
from app.models.device import SmartDevice
from app.schemas.device import SmartDeviceCreate, SmartDeviceUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class CRUDSmartDevice(CRUDBase[SmartDevice, SmartDeviceCreate, SmartDeviceUpdate]):
    async def get_by_user_id(
        self, db: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[SmartDevice]:
        result = await db.execute(
            select(SmartDevice)
            .filter(SmartDevice.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


device = CRUDSmartDevice(SmartDevice)
