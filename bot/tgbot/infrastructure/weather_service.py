"""
Example service demonstrating how to extend BaseAPIService.

This is a template/example for creating new services.
"""

from typing import Optional

from tgbot.infrastructure.base_service import BaseAPIService


class WeatherService(BaseAPIService):
    """Service for weather forecast operations."""

    def __init__(self, base_url: Optional[str] = None, timeout: int = 10):
        """
        Initialize the forecast service.

        Args:
            base_url: Base URL of the backend API. If not provided, uses config.
            timeout: Request timeout in seconds.
        """
        super().__init__(base_url, timeout)

    async def get_forecast(self, city_name: str, days: int = 7) -> str:
        """
        Fetch weather forecast for a city.

        Args:
            city_name: Name of the city to get forecast for.
            days: Number of days to forecast (default: 7).

        Returns:
            Formatted forecast information as a string.
        """
        endpoint = "/weather/current"
        params = {"city": city_name, "days": days}

        status, data = await self._get(endpoint, params)

        # Handle different response scenarios
        if status == 200:
            return self._format_forecast_data(data, city_name, days)
        elif status == 404:
            return f"❌ City '{city_name}' not found. Please check the spelling."
        else:
            return self._handle_error_response(
                status, data, f"fetching forecast for {city_name}"
            )

    def _format_forecast_data(self, data: dict, city_name: str, days: int) -> str:
        """
        Format forecast data into a user-friendly message.

        Args:
            data: Forecast data from the API.
            city_name: Name of the city.
            days: Number of days in the forecast.

        Returns:
            Formatted forecast message.
        """
        try:
            forecast_list = data.get("daily_forecasts", [])
            current_temp = data.get("current_temp", "N/A")
            current_conditions = data.get("current_conditions", "N/A")
            real_city_name = data.get("city_name", city_name)

            message = f"🌤 <b>Weather: {real_city_name}</b>\n"
            message += f"Current: {current_temp}°C, {current_conditions}\n\n"
            message += f"📅 <b>Forecast for {days} days</b>\n\n"

            for day_data in forecast_list[:days]:
                date = day_data.get("date", "N/A")
                max_temp = day_data.get("max_temp", "N/A")
                min_temp = day_data.get("min_temp", "N/A")
                precip_prob = day_data.get("precipitation_prob_max", "0")

                message += f"📆 {date}\n"
                message += f"   🌡 {min_temp}°C .. {max_temp}°C\n"
                message += f"   💧 Precipitation: {precip_prob}%\n\n"

            return message.strip()

        except Exception as e:
            self.logger.error(f"Error formatting forecast data: {e}")
            return "❌ Error formatting forecast data. Please try again."


weather_service = WeatherService()
