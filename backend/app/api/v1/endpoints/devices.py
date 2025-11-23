from typing import Any, List

from app import crud, schemas
from app.api import deps
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/", response_model=List[schemas.SmartDevice])
async def read_devices(
    db: deps.SessionDep,
    skip: int = 0,
    limit: int = 100,
    user_id: int = None,
) -> Any:
    """
    Retrieve smart devices.
    """
    if user_id:
        devices = await crud.device.get_by_user_id(
            db, user_id=user_id, skip=skip, limit=limit
        )
    else:
        devices = await crud.device.get_multi(db, skip=skip, limit=limit)
    return devices


@router.post("/", response_model=schemas.SmartDevice)
async def create_device(
    *,
    db: deps.SessionDep,
    device_in: schemas.SmartDeviceCreate,
) -> Any:
    """
    Create new smart device.
    """
    # Check if user exists
    user = await crud.user.get(db, id=device_in.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    device = await crud.device.create(db, obj_in=device_in)
    return device


@router.get("/{device_id}", response_model=schemas.SmartDevice)
async def read_device(
    *,
    db: deps.SessionDep,
    device_id: int,
) -> Any:
    """
    Get smart device by ID.
    """
    device = await crud.device.get(db, id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.put("/{device_id}", response_model=schemas.SmartDevice)
async def update_device(
    *,
    db: deps.SessionDep,
    device_id: int,
    device_in: schemas.SmartDeviceUpdate,
) -> Any:
    """
    Update a smart device.
    """
    device = await crud.device.get(db, id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device = await crud.device.update(db, db_obj=device, obj_in=device_in)
    return device


@router.delete("/{device_id}", response_model=schemas.SmartDevice)
async def delete_device(
    *,
    db: deps.SessionDep,
    device_id: int,
) -> Any:
    """
    Delete a smart device.
    """
    device = await crud.device.get(db, id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device = await crud.device.remove(db, id=device_id)
    return device
