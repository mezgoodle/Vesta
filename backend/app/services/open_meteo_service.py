import logging
import httpx
from fastapi import HTTPException

from app.schemas.open_meteo import OpenMeteoResponse, DailyForecast

logger = logging.getLogger(__name__)

class OpenMeteoService:
    def __init__(self):
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.forecast_url = "https://api.open-meteo.com/v1/forecast"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def _geocode_city(self, city: str):
        logger.info(
            f"Geocoding city request: {city}",
            extra={"json_fields": {"event": "geocoding_request", "city": city}}
        )
        try:
            response = await self.client.get(
                self.geocoding_url,
                params={"name": city, "count": 1, "language": "en", "format": "json"}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail="Geocoding API error")
            data = response.json()
            if "results" not in data or not data["results"]:
                raise HTTPException(status_code=404, detail=f"City '{city}' not found")
            result = data["results"][0]
            
            logger.info(
                f"Geocoding successful for {city}",
                extra={"json_fields": {"event": "geocoding_success", "city": city, "latitude": result["latitude"], "longitude": result["longitude"]}}
            )
            return result["latitude"], result["longitude"], result["name"]
        except HTTPException as e:
            logger.error(
                f"Geocoding HTTP error for {city}: {e.detail}",
                extra={"json_fields": {"event": "geocoding_error", "city": city, "error": str(e.detail)}}
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected geocoding error for {city}: {str(e)}",
                extra={"json_fields": {"event": "geocoding_error", "city": city, "error": str(e)}}
            )
            raise HTTPException(status_code=500, detail="Unexpected geocoding error")

    async def get_weather(self, city: str, days: int = 7) -> OpenMeteoResponse:
        lat, lon, name = await self._geocode_city(city)
        
        logger.info(
            f"Weather request for {name}",
            extra={"json_fields": {"event": "weather_request", "city": name, "days": days}}
        )
        try:
            response = await self.client.get(
                self.forecast_url,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,weather_code",
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                    "timezone": "auto",
                    "forecast_days": days
                }
            )
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail="Open-Meteo API error")
            data = response.json()
            
            current_data = data.get("current", {})
            daily_data = data.get("daily", {})
            
            daily_forecasts = []
            if "time" in daily_data:
                for i in range(len(daily_data["time"])):
                    daily_forecasts.append(
                        DailyForecast(
                            date=daily_data["time"][i],
                            max_temp=daily_data["temperature_2m_max"][i],
                            min_temp=daily_data["temperature_2m_min"][i],
                            precipitation_prob_max=daily_data["precipitation_probability_max"][i]
                        )
                    )
            
            logger.info(
                f"Weather successful for {name}",
                extra={"json_fields": {"event": "weather_success", "city": name}}
            )
            return OpenMeteoResponse(
                city_name=name,
                current_temp=current_data.get("temperature_2m", 0.0),
                current_conditions=current_data.get("weather_code", ""),
                daily_forecasts=daily_forecasts
            )
        except HTTPException as e:
            logger.error(
                f"Weather HTTP error for {name}: {e.detail}",
                extra={"json_fields": {"event": "weather_error", "city": name, "error": str(e.detail)}}
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected weather error for {name}: {str(e)}",
                extra={"json_fields": {"event": "weather_error", "city": name, "error": str(e)}}
            )
            raise HTTPException(status_code=500, detail="Unexpected weather error")

    async def close(self):
        await self.client.aclose()


open_meteo_service_instance = OpenMeteoService()


def open_meteo_service() -> OpenMeteoService:
    return open_meteo_service_instance
