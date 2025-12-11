from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.weather import WeatherService, weather_service

SessionDep = Annotated[AsyncSession, Depends(get_db)]
WeatherServiceDep = Annotated[WeatherService, Depends(weather_service)]
