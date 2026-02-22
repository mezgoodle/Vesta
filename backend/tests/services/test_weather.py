from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.schemas.weather import WeatherData
from app.services.weather import WeatherService


@pytest.fixture
def mock_httpx_client():
    with patch("app.services.weather.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_settings():
    with patch("app.services.weather.settings") as mock_settings:
        mock_settings.OPENWEATHER_API_KEY = "test-weather-key"
        yield mock_settings


@pytest.mark.asyncio
async def test_get_current_weather_success(mock_httpx_client, mock_settings):
    service = WeatherService()

    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "name": "London",
        "main": {"temp": 15.5, "humidity": 60},
        "weather": [{"description": "cloudy"}],
        "wind": {"speed": 5.0},
    }

    # We need to mock the get method of the client instance
    # Since WeatherService creates a new instance in __init__,
    # mock_httpx_client is the instance returned by the class constructor mock
    mock_httpx_client.get.return_value = mock_response

    weather_data = await service.get_current_weather_by_city_name("London")

    assert isinstance(weather_data, WeatherData)
    assert weather_data.city == "London"
    assert weather_data.temp == 15.5
    assert weather_data.description == "cloudy"
    assert weather_data.humidity == 60
    assert weather_data.wind_speed == 5.0

    mock_httpx_client.get.assert_called_once()
    args, kwargs = mock_httpx_client.get.call_args
    assert kwargs["params"]["q"] == "London"
    assert kwargs["params"]["appid"] == "test-weather-key"
    assert kwargs["params"]["units"] == "metric"


@pytest.mark.asyncio
async def test_get_current_weather_empty_city(mock_httpx_client, mock_settings):
    service = WeatherService()

    with pytest.raises(HTTPException) as exc:
        await service.get_current_weather_by_city_name("")
    assert exc.value.status_code == 400
    assert "City name is required" in exc.value.detail


@pytest.mark.asyncio
async def test_get_current_weather_city_not_found(mock_httpx_client, mock_settings):
    service = WeatherService()

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_httpx_client.get.return_value = mock_response

    with pytest.raises(HTTPException) as exc:
        await service.get_current_weather_by_city_name("UnknownCity")
    assert exc.value.status_code == 404
    assert "not found" in exc.value.detail


@pytest.mark.asyncio
async def test_get_current_weather_api_error(mock_httpx_client, mock_settings):
    service = WeatherService()

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_httpx_client.get.return_value = mock_response

    with pytest.raises(HTTPException) as exc:
        await service.get_current_weather_by_city_name("London")
    assert exc.value.status_code == 502
    assert "OpenWeatherMap API error" in exc.value.detail


@pytest.mark.asyncio
async def test_get_current_weather_invalid_response(mock_httpx_client, mock_settings):
    service = WeatherService()

    mock_response = MagicMock()
    mock_response.status_code = 200
    # Missing required fields
    mock_response.json.return_value = {"name": "London"}
    mock_httpx_client.get.return_value = mock_response

    with pytest.raises(HTTPException) as exc:
        await service.get_current_weather_by_city_name("London")
    assert exc.value.status_code == 502
    assert "Invalid response structure" in exc.value.detail


@pytest.mark.asyncio
async def test_get_current_weather_unexpected_error(mock_httpx_client, mock_settings):
    service = WeatherService()

    mock_httpx_client.get.side_effect = Exception("Network Error")

    with pytest.raises(HTTPException) as exc:
        await service.get_current_weather_by_city_name("London")
    assert exc.value.status_code == 500
    assert "Unexpected error" in exc.value.detail


@pytest.mark.asyncio
async def test_close_client(mock_httpx_client, mock_settings):
    service = WeatherService()
    await service.close()
    mock_httpx_client.aclose.assert_called_once()
