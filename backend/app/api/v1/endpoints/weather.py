from fastapi import APIRouter

from app.api.deps import CurrentUser, WeatherServiceDep
from app.schemas.weather import WeatherData

router = APIRouter()


@router.get("/current", response_model=WeatherData)
async def get_current_weather(
    city: str,
    service: WeatherServiceDep,
    current_user: CurrentUser,
) -> WeatherData:
    """
    Get current weather data for a city.

    Args:
        city: Name of the city to fetch weather for
        service: Injected WeatherService instance

    Returns:
        WeatherData: Current weather information including temperature (Celsius),
                     description, humidity, and wind speed
    """
    return await service.get_current_weather_by_city_name(city)
