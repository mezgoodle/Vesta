# Architecture Overview

This module demonstrates the Abstract Base Service pattern used in the Vesta Bot infrastructure.

## Design Pattern: Template Method + Inheritance

```text
┌─────────────────────────────────────────────────────────────┐
│                       BaseAPIService (ABC)                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │       Protected HTTP Methods (Template Methods)       │  │
│  │  • _get(endpoint, params) -> (status, data)          │  │
│  │  • _post(endpoint, json_data) -> (status, data)      │  │
│  │  • _put(endpoint, json_data) -> (status, data)       │  │
│  │  • _delete(endpoint) -> (status, data)                │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    Common Utilities                   │  │
│  │  • _handle_error_response(status, data, context)      │  │
│  │  • logger (per-service logging)                       │  │
│  │  • timeout configuration                              │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                               ▲
                               │ (inherits)
                               │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
            │                   │                   │
    ┌───────▼────────┐  ┌───────▼────────┐  ┌──────▼──────┐
    │ WeatherService │  │ ForecastService│  │ AlertService│
    ├────────────────┤  ├────────────────┤  ├─────────────┤
    │ Public API:    │  │ Public API:    │  │ Public API: │
    │ • get_current_ │  │ • get_forecast │  │ • get_alerts│
    │   weather()    │  │   ()           │  │   ()        │
    ├────────────────┤  ├────────────────┤  ├─────────────┤
    │ Private:       │  │ Private:       │  │ Private:    │
    │ • _format_     │  │ • _format_     │  │ • _format_  │
    │   weather_data │  │   forecast_data│  │   alerts    │
    └────────────────┘  └────────────────┘  └─────────────┘
```

## Benefits of This Pattern

1.  **Code Reuse**
    *   HTTP communication logic is written once in `BaseAPIService`.
    *   All concrete services inherit the capability automatically.
    *   Zero duplication of client setup or request boilerplate.

2.  **Consistency**
    *   All services interact with the backend in an identical manner.
    *   Uniform error handling maps network anomalies to clear user warnings.
    *   Standardized logging profiles service execution times.

3.  **Testability**
    *   Mocking network operations is simplified by overriding the base class's HTTP wrappers.
    *   Individual service formatters and business rules can be verified in isolation.

4.  **Maintainability**
    *   Changes to base connection pools, headers, or timeouts occur in a single location.
    *   Derived services focus strictly on parsing specific backend payload mappings.

5.  **Extensibility**
    *   New API endpoints can be supported quickly by subclassing `BaseAPIService` and defining domain-specific public methods.

---

## Code Example: Subclassing BaseAPIService

```python
from typing import Optional
from tgbot.infrastructure.base_service import BaseAPIService

class UserService(BaseAPIService):
    """Service for user operations."""

    async def get_user_profile(self, user_id: int) -> str:
        endpoint = f"/users/{user_id}"
        status, data = await self._get(endpoint)

        if status == 200:
            return self._format_user_data(data)
        else:
            return self._handle_error_response(status, data, "fetching user profile")

    def _format_user_data(self, data: dict) -> str:
        # Custom logic formatting details into Markdown messages
        return f"👤 User {data.get('id')}: {data.get('email', 'No Email')}"

# Instantiate as a singleton for injection
user_service = UserService()
```

---

## Design Comparison: Composition vs. Inheritance

### Composition (Has-A Relationship)
```python
class WeatherService:
    def __init__(self):
        self.api_client = VestaAPIClient()  # Delegation

    async def get_weather(self, city):
        return await self.api_client.get(...)
```
*   **Pros**: Highly flexible, decoupled.
*   **Cons**: Introduces extra delegation boilerplate. Harder to enforce uniform error routines across many distinct service wrappers.

### Inheritance (Is-A Relationship)
```python
class WeatherService(BaseAPIService):
    async def get_weather(self, city):
        return await self._get(...)  # Direct protected access
```
*   **Pros**: Extremely clean codebase. Consistent logging and error patterns are inherited by design.
*   **Cons**: Moderate coupling to the base class (ideal and highly acceptable for tightly-coupled internal microservice clients).

---

## Conclusion
For Vesta's architecture, **Inheritance** provides the optimal balance. All clients operate under the exact same API context, share standard configurations, and inherit identical HTTP handlers. This leads to a highly maintainable, elegant, and Pythonic code structure.
