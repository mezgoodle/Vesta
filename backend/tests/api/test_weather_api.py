import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock
from fastapi import HTTPException

from app.core.config import settings
from app.main import app
from app.api.deps import open_meteo_service
from app.schemas.open_meteo import OpenMeteoResponse, DailyForecast


@pytest.fixture
def mock_open_meteo_service():
    mock_svc = AsyncMock()
    app.dependency_overrides[open_meteo_service] = lambda: mock_svc
    yield mock_svc
    app.dependency_overrides.pop(open_meteo_service, None)


@pytest.mark.asyncio
async def test_get_current_weather_success(
    client: AsyncClient, mock_open_meteo_service, auth_user: dict
) -> None:
    headers = auth_user["headers"]

    mock_response = OpenMeteoResponse(
        city_name="Kyiv",
        current_temp=15.0,
        current_conditions="Sunny",
        daily_forecasts=[
            DailyForecast(
                date="2026-04-14", max_temp=20.0, min_temp=10.0, precipitation_prob_max=0
            )
        ],
    )
    mock_open_meteo_service.get_weather.return_value = mock_response

    response = await client.get(
        f"{settings.API_V1_STR}/weather/current",
        params={"city": "Kyiv", "days": 5},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["city_name"] == "Kyiv"
    assert data["current_temp"] == 15.0
    assert data["current_conditions"] == "Sunny"
    assert len(data["daily_forecasts"]) == 1

    mock_open_meteo_service.get_weather.assert_called_once_with("Kyiv", 5)


@pytest.mark.asyncio
async def test_get_current_weather_default_days(
    client: AsyncClient, mock_open_meteo_service, auth_user: dict
) -> None:
    headers = auth_user["headers"]

    mock_response = OpenMeteoResponse(
        city_name="Kyiv",
        current_temp=15.0,
        current_conditions="Sunny",
        daily_forecasts=[],
    )
    mock_open_meteo_service.get_weather.return_value = mock_response

    response = await client.get(
        f"{settings.API_V1_STR}/weather/current",
        params={"city": "Kyiv"},
        headers=headers,
    )

    assert response.status_code == 200
    mock_open_meteo_service.get_weather.assert_called_once_with("Kyiv", 7)


@pytest.mark.asyncio
async def test_get_current_weather_unauthorized(client: AsyncClient) -> None:
    response = await client.get(
        f"{settings.API_V1_STR}/weather/current", params={"city": "Kyiv"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_weather_api_failure(
    client: AsyncClient, mock_open_meteo_service, auth_user: dict
) -> None:
    headers = auth_user["headers"]

    mock_open_meteo_service.get_weather.side_effect = HTTPException(
        status_code=502, detail="Open-Meteo API error"
    )

    response = await client.get(
        f"{settings.API_V1_STR}/weather/current",
        params={"city": "Kyiv"},
        headers=headers,
    )

    assert response.status_code == 502
    data = response.json()
    assert "Open-Meteo API error" in data["detail"]
