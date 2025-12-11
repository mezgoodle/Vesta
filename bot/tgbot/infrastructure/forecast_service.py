"""
Example service demonstrating how to extend BaseAPIService.

This is a template/example for creating new services.
"""

from typing import Optional

from tgbot.infrastructure.base_service import BaseAPIService


class ForecastService(BaseAPIService):
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
        endpoint = "/api/v1/weather/forecast"
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
            # Example formatting - adjust based on your API response
            forecast_list = data.get("forecast", [])

            message = f"📅 **{days}-Day Forecast for {city_name.title()}**\n\n"

            for day_data in forecast_list[:days]:
                date = day_data.get("date", "N/A")
                temp_max = day_data.get("temp_max", "N/A")
                temp_min = day_data.get("temp_min", "N/A")
                description = day_data.get("description", "N/A")

                message += f"📆 {date}\n"
                message += f"   🌡 {temp_min}°C - {temp_max}°C\n"
                message += f"   📝 {description.capitalize()}\n\n"

            return message.strip()

        except Exception as e:
            self.logger.error(f"Error formatting forecast data: {e}")
            return "❌ Error formatting forecast data. Please try again."


# Create a singleton instance
forecast_service = ForecastService()
