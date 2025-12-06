# Vesta API Infrastructure

This module provides a professional OOP-based integration with the Vesta Backend API for the Telegram Bot.

## Architecture

The infrastructure uses an **Abstract Base Service Pattern** with inheritance for clean, maintainable, and testable code.

### Design Pattern: Template Method + Inheritance

```
BaseAPIService (Abstract)
    ├── _get()          # Protected HTTP methods
    ├── _post()
    ├── _put()
    ├── _delete()
    └── _handle_error_response()
         ↑
         │ (inherits)
         │
    WeatherService
    ForecastService
    ... (other services)
```

### Components

#### 1. **BaseAPIService** (`base_service.py`)

Abstract base class providing common HTTP functionality.

**Features:**

- Protected HTTP methods (`_get`, `_post`, `_put`, `_delete`)
- Automatic error handling and logging
- Configurable timeout and base URL
- Common error response handling

**Why Abstract?**

- Enforces consistent API interaction patterns
- Reduces code duplication
- Makes testing easier (mock once, use everywhere)
- Provides a clear contract for all services

#### 2. **WeatherService** (`weather_service.py`)

Concrete service for weather operations.

**Features:**

- Inherits HTTP methods from `BaseAPIService`
- Implements weather-specific business logic
- Formats weather data for users
- Custom error messages for weather context

#### 3. **ForecastService** (`forecast_service.py`)

Example service demonstrating the pattern.

**Purpose:**

- Shows how to create new services
- Template for extending functionality

## Configuration

Add the backend URL to your `.env` file:

```env
BACKEND_BASE_URL=http://localhost:8000
```

If not specified, it defaults to `http://localhost:8000`.

## Usage

### Using Existing Services

```python
from tgbot.infrastructure.weather_service import weather_service

# Fetch weather data
weather_info = await weather_service.get_current_weather("London")
print(weather_info)
```

### Creating a New Service

```python
from typing import Optional
from tgbot.infrastructure.base_service import BaseAPIService

class AlertService(BaseAPIService):
    """Service for weather alerts."""

    def __init__(self, base_url: Optional[str] = None, timeout: int = 10):
        super().__init__(base_url, timeout)

    async def get_alerts(self, city_name: str) -> str:
        """Fetch weather alerts for a city."""
        endpoint = "/api/v1/weather/alerts"
        params = {"city": city_name}

        status, data = await self._get(endpoint, params)

        if status == 200:
            return self._format_alerts(data)
        else:
            return self._handle_error_response(status, data, "fetching alerts")

    def _format_alerts(self, data: dict) -> str:
        """Format alert data."""
        # Your formatting logic here
        pass

# Create singleton
alert_service = AlertService()
```

### In a Handler

```python
from aiogram import types
from tgbot.infrastructure.weather_service import weather_service

async def weather_handler(message: types.Message):
    city = message.get_args()
    weather = await weather_service.get_current_weather(city)
    await message.reply(weather)
```

## OOP Principles Applied

### 1. **Inheritance**

Services inherit common HTTP functionality from `BaseAPIService`.

### 2. **Encapsulation**

- Protected methods (`_get`, `_post`) indicate internal API
- Public methods (`get_current_weather`) are the service interface

### 3. **Single Responsibility**

- `BaseAPIService`: HTTP communication
- `WeatherService`: Weather business logic
- Each service: One domain of functionality

### 4. **Open/Closed Principle**

- Open for extension (create new services)
- Closed for modification (don't change base class)

### 5. **Dependency Inversion**

- Services depend on abstraction (`BaseAPIService`)
- Easy to mock for testing

## Error Handling

The base service handles common scenarios:

1. **Backend Offline (status = 0)**: "❌ My brain is offline. Please try again later."
2. **Not Found (404)**: "❌ Resource not found. Please check your input."
3. **Bad Request (400)**: "❌ Invalid request. Please try again."
4. **Server Error (500)**: "❌ Server error. Please try again later."
5. **Network Timeout**: 10-second timeout (configurable)

Services can override `_handle_error_response()` for custom error handling.

## API Response Format

### Weather Endpoint

```json
{
  "temperature": 15.5,
  "feels_like": 13.2,
  "description": "partly cloudy",
  "humidity": 65,
  "wind_speed": 3.5,
  "pressure": 1013
}
```

## Features

- ✅ Professional OOP design with inheritance
- ✅ Abstract base class for consistency
- ✅ Protected methods for encapsulation
- ✅ Async/await support with `aiohttp`
- ✅ Automatic timeout handling (configurable)
- ✅ Comprehensive error handling
- ✅ Detailed logging per service
- ✅ Singleton pattern for easy reuse
- ✅ Type hints for IDE support
- ✅ Easy to extend and test

## Testing

### Unit Testing Example

```python
import pytest
from unittest.mock import AsyncMock
from tgbot.infrastructure.weather_service import WeatherService

@pytest.mark.asyncio
async def test_weather_service():
    service = WeatherService()

    # Mock the _get method
    service._get = AsyncMock(return_value=(200, {
        "temperature": 15.5,
        "feels_like": 13.2,
        "description": "partly cloudy",
        "humidity": 65,
        "wind_speed": 3.5,
        "pressure": 1013
    }))

    result = await service.get_current_weather("London")
    assert "London" in result
    assert "15.5°C" in result
```

### Integration Testing

1. Ensure your backend is running at the configured URL
2. Use the `/weather` command in Telegram: `/weather London`
3. Check logs for any errors

## Advantages Over Composition

| Aspect          | Composition (Old)            | Inheritance (New)       |
| --------------- | ---------------------------- | ----------------------- |
| Code Reuse      | Manual delegation            | Automatic inheritance   |
| Consistency     | Each service implements HTTP | Enforced by base class  |
| Testing         | Mock client in each service  | Mock once in base class |
| Extensibility   | Add methods to client        | Override base methods   |
| Maintainability | Changes affect all services  | Changes in one place    |

## Dependencies

- `aiohttp` - Async HTTP client
- `pydantic-settings` - Configuration management

All dependencies are listed in `requirements.txt`.

## Best Practices

1. **Always inherit from `BaseAPIService`** when creating new services
2. **Use protected methods (`_get`, `_post`)** for HTTP calls
3. **Implement public methods** for business logic
4. **Override `_handle_error_response()`** for custom error handling
5. **Create singletons** for services that don't need multiple instances
6. **Add type hints** for better IDE support and documentation
