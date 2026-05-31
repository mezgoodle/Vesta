# Vesta API Infrastructure

This module provides a professional, OOP-based API integration with the Vesta Backend API for the Telegram Bot.

---

## 📐 Architecture

The infrastructure uses an **Abstract Base Service Pattern** with inheritance to produce clean, maintainable, and testable code.

```text
BaseAPIService (Abstract)
    ├── _get()          # Protected async HTTP methods
    ├── _post()
    ├── _put()
    ├── _delete()
    └── _handle_error_response()
         ▲
         │ (inherits)
         │
    ┌────┴────────────────────────┐
    │                             │
WeatherService              CalendarService   ... (other services)
```

---

## 🧱 Key Components

### 1. **BaseAPIService** (`base_service.py`)
Abstract base class providing common HTTP and connection lifecycle management.
*   **Protected HTTP wrappers**: Handles asynchronous `_get`, `_post`, `_put`, and `_delete` requests via `aiohttp`.
*   **Centralized Error Handling**: Automatically converts network timeouts or HTTP errors into user-friendly error logs and alerts.
*   **Service-to-Service Authorization**: Injects the required standard `X-API-Key` headers into all outgoing requests.

### 2. **WeatherService** (`weather_service.py`)
Extends `BaseAPIService` to parse OpenMeteo forecast objects and format outputs.
*   Converts JSON responses into standard telegram card layouts.
*   Handles errors specifically within geocoding or forecast bounds.

### 3. **CalendarService** (`calendar_service.py`)
Extends `BaseAPIService` to coordinate event fetch/insert queries.

### 4. **LLMService** (`llm_service.py`)
Extends `BaseAPIService` to transmit chat prompts to the backend's Google ADK endpoint under `/chat/process`. Supports voice streaming integrations.

### 5. **UserService** (`user_service.py`)
Extends `BaseAPIService` to list approved users, trigger permissions updates, or generate calendar consent links.

---

## ⚙️ Configuration

Set the backend base url inside the bot's `.env` configuration:
```env
BACKEND_BASE_URL=http://localhost:8000
```
If not specified, the system defaults to `http://localhost:8000`.

---

## 📡 API Response Format

### Weather Endpoint Forecast Schema (`/weather/current`)
The endpoint queries the OpenMeteo engine and returns the following structure:

```json
{
  "city_name": "London",
  "current_temp": 15.5,
  "current_conditions": "Partly cloudy",
  "daily_forecasts": [
    {
      "date": "2026-05-31",
      "max_temp": 18.2,
      "min_temp": 12.1,
      "precipitation_prob_max": 20
    },
    {
      "date": "2026-06-01",
      "max_temp": 19.5,
      "min_temp": 11.8,
      "precipitation_prob_max": 10
    }
  ]
}
```

---

## 🛠️ Adding a New Service

To integrate a new API endpoint area, extend `BaseAPIService`:

```python
from typing import Optional
from tgbot.infrastructure.base_service import BaseAPIService

class AlertService(BaseAPIService):
    """Service for handling smart alerts."""

    def __init__(self, base_url: Optional[str] = None, timeout: int = 10):
        super().__init__(base_url, timeout)

    async def get_active_alerts(self, city_name: str) -> str:
        endpoint = "/alerts/active"
        params = {"city": city_name}

        status, data = await self._get(endpoint, params)

        if status == 200:
            return self._format_alerts(data)
        else:
            return self._handle_error_response(status, data, "fetching active alerts")

    def _format_alerts(self, data: dict) -> str:
        # Construct and return human-readable Markdown lists
        return f"⚠️ Alert: {data.get('title')} - {data.get('description')}"

# Instantiate as a singleton for export
alert_service = AlertService()
```

---

## 🧪 Testing Services

### Unit Testing Client Service Logic
Mocking backend responses is simple using `unittest.mock.AsyncMock`:

```python
import pytest
from unittest.mock import AsyncMock
from tgbot.infrastructure.weather_service import WeatherService

@pytest.mark.asyncio
async def test_weather_service_parsing():
    service = WeatherService()

    # Mock the internal protected _get method
    service._get = AsyncMock(return_value=(200, {
        "city_name": "London",
        "current_temp": 15.5,
        "current_conditions": "Partly cloudy",
        "daily_forecasts": [
            {
                "date": "2026-05-31",
                "max_temp": 18.2,
                "min_temp": 12.1,
                "precipitation_prob_max": 20
            }
        ]
    }))

    result = await service.get_forecast("London", days=1)
    assert "London" in result
    assert "15.5°C" in result
```
