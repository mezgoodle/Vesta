from fastapi import APIRouter

from app.api.deps import CurrentUser, OpenMeteoServiceDep
from app.schemas.open_meteo import OpenMeteoResponse

router = APIRouter()


@router.get("/current", response_model=OpenMeteoResponse)
async def get_current_weather(
    city: str,
    service: OpenMeteoServiceDep,
    current_user: CurrentUser,
) -> OpenMeteoResponse:
    """
    Get current weather data and forecast for a city.

    Args:
        city: Name of the city to fetch weather for
        service: Injected OpenMeteoService instance
        current_user: Authenticated user (required)

    Returns:
        OpenMeteoResponse: Current weather conditions and 7-day forecast
    """
    return await service.get_weather(city)
