from pydantic import BaseModel, Field


class WeatherData(BaseModel):
    city: str = Field(..., description="City name")
    temp: float = Field(..., description="Temperature in Celsius")
    description: str = Field(..., description="Weather description")
    humidity: int = Field(..., description="Humidity percentage")
    wind_speed: float = Field(..., description="Wind speed in m/s")

    model_config = {"from_attributes": True}
