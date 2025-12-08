from tgbot.infrastructure.base_service import BaseAPIService


class WeatherService(BaseAPIService):
    """Service for weather-related operations."""

    def __init__(self, base_url: str | None = None, timeout: int = 10):
        super().__init__(base_url, timeout)

    async def get_current_weather(self, city_name: str) -> str:
        """
        Fetch current weather data for a city.

        Args:
            city_name: Name of the city to get weather for.

        Returns:
            Formatted weather information as a string.
        """
        endpoint = "/api/v1/weather/current"
        params = {"city": city_name}

        status, data = await self._get(endpoint, params)

        # Handle different response scenarios
        if status == 200:
            return self._format_weather_data(data, city_name)
        elif status == 404:
            return f"❌ City '{city_name}' not found. Please check the spelling."
        else:
            return self._handle_error_response(
                status, data, f"fetching weather for {city_name}"
            )

    def _format_weather_data(self, data: dict, city_name: str) -> str:
        """
        Format weather data into a user-friendly message.

        Args:
            data: Weather data from the API.
            city_name: Name of the city.

        Returns:
            Formatted weather message.
        """
        try:
            # Extract data from the response
            temp = data.get("temp", "N/A")
            description = data.get("description", "N/A")
            humidity = data.get("humidity", "N/A")
            wind_speed = data.get("wind_speed", "N/A")

            # Format the message
            message = f"🌤 <b>Weather in {city_name.title()}</b>\n\n"
            message += f"🌡 Temperature: {temp}°C\n"
            message += f"📝 Description: {description.capitalize()}\n"
            message += f"💧 Humidity: {humidity}%\n"
            message += f"💨 Wind Speed: {wind_speed} m/s\n"

            return message

        except Exception as e:
            self.logger.error(f"Error formatting weather data: {e}")
            return "❌ Error formatting weather data. Please try again."


weather_service = WeatherService()
