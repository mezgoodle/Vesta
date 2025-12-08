import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.schemas.weather import WeatherData


class WeatherService:
    """

    Service for fetching weather data from OpenWeatherMap API.

    Docs: https://openweathermap.org/api
    """

    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY

        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_current_weather_by_city_name(self, city: str) -> WeatherData:
        """

        Fetch current weather data for a given city.


        Args:

            city: Name of the city to fetch weather for


        Returns:

            WeatherData: Standardized weather information


        Raises:

            HTTPException: If city not found, API error, or unexpected error occurs
        """
        try:
            response = await self.client.get(
                self.base_url,
                params={
                    "q": city,
                    "appid": self.api_key,
                    "units": "metric",  # Use Celsius
                },
            )

            # Handle city not found

            if response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"City '{city}' not found",
                )

            # Handle other API errors

            if response.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"OpenWeatherMap API error: {response.status_code}",
                )

            data = response.json()

            # Extract and transform data to our schema

            weather_data = WeatherData(
                city=data["name"],
                temp=data["main"]["temp"],
                description=data["weather"][0]["description"],
                humidity=data["main"]["humidity"],
                wind_speed=data["wind"]["speed"],
            )

            return weather_data

        except HTTPException:
            # Re-raise HTTP exceptions
            raise

        except Exception as e:
            # Handle unexpected errors

            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error fetching weather data: {str(e)}",
            )

    async def close(self):
        await self.client.aclose()


async def weather_service():
    service = WeatherService()
    try:
        yield service
    finally:
        await service.close()
