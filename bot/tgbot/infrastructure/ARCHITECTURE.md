"""
Architecture Overview
=====================

This module demonstrates the Abstract Base Service pattern used in the Vesta Bot infrastructure.

## Design Pattern: Template Method + Inheritance

┌─────────────────────────────────────────────────────────────┐
│ BaseAPIService (ABC) │
│ ┌───────────────────────────────────────────────────────┐ │
│ │ Protected HTTP Methods (Template Methods) │ │
│ │ • _get(endpoint, params) -> (status, data) │ │
│ │ • \_post(endpoint, json_data) -> (status, data) │ │
│ │ • \_put(endpoint, json_data) -> (status, data) │ │
│ │ • \_delete(endpoint) -> (status, data) │ │
│ └───────────────────────────────────────────────────────┘ │
│ ┌───────────────────────────────────────────────────────┐ │
│ │ Common Utilities │ │
│ │ • \_handle_error_response(status, data, context) │ │
│ │ • logger (per-service logging) │ │
│ │ • timeout configuration │ │
│ └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
▲
│ (inherits)
│
┌───────────────────┼───────────────────┐
│ │ │
│ │ │
┌───────▼────────┐ ┌───────▼────────┐ ┌──────▼──────┐
│ WeatherService │ │ ForecastService│ │ AlertService│
├────────────────┤ ├────────────────┤ ├─────────────┤
│ Public API: │ │ Public API: │ │ Public API: │
│ • get_current_ │ │ • get*forecast │ │ • get_alerts│
│ weather() │ │ () │ │ () │
├────────────────┤ ├────────────────┤ ├─────────────┤
│ Private: │ │ Private: │ │ Private: │
│ • \_format* │ │ • _format_ │ │ • _format_ │
│ weather_data │ │ forecast_data│ │ alerts │
└────────────────┘ └────────────────┘ └─────────────┘

## Benefits of This Pattern

1. Code Reuse

   - HTTP logic written once in BaseAPIService
   - All services inherit automatically
   - No code duplication

2. Consistency

   - All services use the same HTTP methods
   - Uniform error handling
   - Standardized logging

3. Testability

   - Mock BaseAPIService methods once
   - Test business logic separately
   - Easy to create test doubles

4. Maintainability

   - Changes to HTTP logic in one place
   - Services focus on business logic
   - Clear separation of concerns

5. Extensibility
   - Add new services by inheriting
   - Override methods for custom behavior
   - No need to modify existing code

## Example: Creating a New Service

from tgbot.infrastructure.base_service import BaseAPIService

class UserService(BaseAPIService):
'''Service for user operations.'''

    async def get_user_profile(self, user_id: int) -> str:
        endpoint = f"/api/v1/users/{user_id}"
        status, data = await self._get(endpoint)

        if status == 200:
            return self._format_user_data(data)
        else:
            return self._handle_error_response(status, data, "fetching user profile")

    def _format_user_data(self, data: dict) -> str:
        # Format user data for display
        pass

# Create singleton

user_service = UserService()

## Comparison: Composition vs Inheritance

Composition (Old Approach):
class WeatherService:
def **init**(self):
self.api_client = VestaAPIClient() # Has-a relationship

        async def get_weather(self, city):
            return await self.api_client.get(...)  # Delegation

    Pros: Flexibility, loose coupling
    Cons: More boilerplate, manual delegation, harder to enforce consistency

Inheritance (New Approach):
class WeatherService(BaseAPIService): # Is-a relationship
async def get_weather(self, city):
return await self.\_get(...) # Direct access

    Pros: Less code, enforced consistency, easier testing
    Cons: Tighter coupling (acceptable for internal API)

## When to Use Each

Use Inheritance (Current Approach) when:

- Services share common behavior (HTTP calls)
- You want to enforce a contract
- Services are part of the same domain (API services)
- You control both base and derived classes

Use Composition when:

- Combining unrelated behaviors
- Need runtime flexibility
- Working with external libraries
- Multiple inheritance would be needed

## Conclusion

For our use case (API services), inheritance is the better choice because:

1. All services need HTTP functionality
2. We want consistent error handling
3. Services are tightly related (all call Vesta API)
4. Easier to maintain and extend
5. More professional and Pythonic
   """
