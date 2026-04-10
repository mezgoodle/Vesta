from typing import List, Union
from pydantic import BaseModel

class DailyForecast(BaseModel):
    date: str
    max_temp: float
    min_temp: float
    precipitation_prob_max: int

class OpenMeteoResponse(BaseModel):
    city_name: str
    current_temp: float
    current_conditions: Union[str, int]
    daily_forecasts: List[DailyForecast]
