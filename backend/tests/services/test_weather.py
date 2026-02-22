
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.services.weather import WeatherService
from app.schemas.weather import WeatherData

@pytest.fixture
async def weather_service():
    service = WeatherService()
    yield service
    await service.close()

@pytest.mark.asyncio
async def test_get_current_weather_success(weather_service):
    """Test successful weather data retrieval."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "name": "London",
        "main": {
            "temp": 15.5,
            "humidity": 72
        },
        "weather": [
            {"description": "scattered clouds"}
        ],
        "wind": {
            "speed": 3.6
        }
    }

    with patch.object(weather_service.client, 'get', return_value=mock_response) as mock_get:
        result = await weather_service.get_current_weather_by_city_name("London")

        assert isinstance(result, WeatherData)
        assert result.city == "London"
        assert result.temp == 15.5
        assert result.description == "scattered clouds"
        assert result.humidity == 72
        assert result.wind_speed == 3.6

        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert kwargs["params"]["q"] == "London"
        assert kwargs["params"]["units"] == "metric"

@pytest.mark.asyncio
async def test_get_current_weather_city_not_found(weather_service):
    """Test behavior when city is not found."""
    mock_response = MagicMock()
    mock_response.status_code = 404

    with patch.object(weather_service.client, 'get', return_value=mock_response):
        with pytest.raises(HTTPException) as excinfo:
            await weather_service.get_current_weather_by_city_name("NonExistentCity")

        assert excinfo.value.status_code == 404
        assert "not found" in excinfo.value.detail

@pytest.mark.asyncio
async def test_get_current_weather_api_error(weather_service):
    """Test behavior when API returns an error."""
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch.object(weather_service.client, 'get', return_value=mock_response):
        with pytest.raises(HTTPException) as excinfo:
            await weather_service.get_current_weather_by_city_name("London")

        assert excinfo.value.status_code == 502
        assert "OpenWeatherMap API error" in excinfo.value.detail

@pytest.mark.asyncio
async def test_get_current_weather_invalid_response(weather_service):
    """Test behavior when API returns invalid JSON structure."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"invalid": "data"}

    with patch.object(weather_service.client, 'get', return_value=mock_response):
        with pytest.raises(HTTPException) as excinfo:
            await weather_service.get_current_weather_by_city_name("London")

        assert excinfo.value.status_code == 502
        assert "Invalid response structure" in excinfo.value.detail

@pytest.mark.asyncio
async def test_get_current_weather_empty_city(weather_service):
    """Test validation for empty city name."""
    with pytest.raises(HTTPException) as excinfo:
        await weather_service.get_current_weather_by_city_name("")

    assert excinfo.value.status_code == 400
    assert "City name is required" in excinfo.value.detail

@pytest.mark.asyncio
async def test_get_current_weather_unexpected_exception(weather_service):
    """Test unexpected exception handling."""
    with patch.object(weather_service.client, 'get', side_effect=Exception("Connection error")):
        with pytest.raises(HTTPException) as excinfo:
            await weather_service.get_current_weather_by_city_name("London")

        assert excinfo.value.status_code == 500
        assert "Unexpected error" in excinfo.value.detail
