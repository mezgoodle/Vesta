import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException

from app.services.open_meteo_service import OpenMeteoService
from app.schemas.open_meteo import OpenMeteoResponse, DailyForecast


@pytest.fixture
def meteo_service():
    with patch("app.services.open_meteo_service.httpx.AsyncClient") as mock_client:
        service = OpenMeteoService()
        service.client = MagicMock()
        service.client.get = AsyncMock()
        service.client.aclose = AsyncMock()
        return service


@pytest.mark.asyncio
async def test_geocode_city_success(meteo_service):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [{"latitude": 50.45, "longitude": 30.52, "name": "Kyiv"}]
    }
    meteo_service.client.get.return_value = mock_response

    lat, lon, name = await meteo_service._geocode_city("Kyiv")

    assert lat == 50.45
    assert lon == 30.52
    assert name == "Kyiv"
    meteo_service.client.get.assert_called_once()


@pytest.mark.asyncio
async def test_geocode_city_failure_502(meteo_service):
    mock_response = MagicMock()
    mock_response.status_code = 500
    meteo_service.client.get.return_value = mock_response

    with pytest.raises(HTTPException) as exc_info:
        await meteo_service._geocode_city("Kyiv")

    assert exc_info.value.status_code == 502
    assert "Geocoding API error" in exc_info.value.detail


@pytest.mark.asyncio
async def test_geocode_city_failure_404(meteo_service):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}
    meteo_service.client.get.return_value = mock_response

    with pytest.raises(HTTPException) as exc_info:
        await meteo_service._geocode_city("UnknownCity")

    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_geocode_city_failure_500_exception(meteo_service):
    meteo_service.client.get.side_effect = Exception("Network Error")

    with pytest.raises(HTTPException) as exc_info:
        await meteo_service._geocode_city("Kyiv")

    assert exc_info.value.status_code == 500
    assert "Unexpected geocoding error" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_weather_success(meteo_service):
    # Mocking `_geocode_city` and `client.get` for the forecast
    with patch.object(
        meteo_service, "_geocode_city", new_callable=AsyncMock
    ) as mock_geocode:
        mock_geocode.return_value = (50.45, 30.52, "Kyiv")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "current": {"temperature_2m": 15.5, "weather_code": 1},
            "daily": {
                "time": ["2026-04-11"],
                "temperature_2m_max": [20.0],
                "temperature_2m_min": [10.0],
                "precipitation_probability_max": [0],
            },
        }
        meteo_service.client.get.return_value = mock_response

        response = await meteo_service.get_weather("Kyiv", days=1)

        assert isinstance(response, OpenMeteoResponse)
        assert response.city_name == "Kyiv"
        assert response.current_temp == 15.5
        assert response.current_conditions == 1
        assert len(response.daily_forecasts) == 1
        assert isinstance(response.daily_forecasts[0], DailyForecast)
        assert response.daily_forecasts[0].date == "2026-04-11"
        assert response.daily_forecasts[0].max_temp == 20.0

        meteo_service.client.get.assert_called_once()
        mock_geocode.assert_called_with("Kyiv")


@pytest.mark.asyncio
async def test_get_weather_api_failure_502(meteo_service):
    with patch.object(
        meteo_service, "_geocode_city", new_callable=AsyncMock
    ) as mock_geocode:
        mock_geocode.return_value = (50.45, 30.52, "Kyiv")

        mock_response = MagicMock()
        mock_response.status_code = 400
        meteo_service.client.get.return_value = mock_response

        with pytest.raises(HTTPException) as exc_info:
            await meteo_service.get_weather("Kyiv")

        assert exc_info.value.status_code == 502
        assert "Open-Meteo API error" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_weather_unexpected_error(meteo_service):
    with patch.object(
        meteo_service, "_geocode_city", new_callable=AsyncMock
    ) as mock_geocode:
        mock_geocode.return_value = (50.45, 30.52, "Kyiv")
        meteo_service.client.get.side_effect = Exception("Unknown")

        with pytest.raises(HTTPException) as exc_info:
            await meteo_service.get_weather("Kyiv")

        assert exc_info.value.status_code == 500
        assert "Unexpected weather error" in exc_info.value.detail


@pytest.mark.asyncio
async def test_close(meteo_service):
    await meteo_service.close()
    meteo_service.client.aclose.assert_called_once()
