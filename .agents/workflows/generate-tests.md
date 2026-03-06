---
description: How to generate unit tests for the backend
---

## Testing Workflow

- **Test-Driven Intent:** For every new feature, implementation MUST be accompanied by unit tests.
- **File Naming:** Tests must follow the pattern:
  - `app/services/my_service.py` -> `tests/services/test_my_service.py`
  - `app/api/v1/endpoints/my_router.py` -> `tests/api/v1/test_my_router.py`
- **Method Coverage:** Every public method in a class or endpoint function must have a corresponding test case covering:
  - Success path (200 OK / expected result).
  - Failure path (404/400/500 errors or exceptions).
- **Mocking:**
  - External APIs (Gemini, Google Drive, etc.) must be mocked using `unittest.mock.AsyncMock` or `pytest-mock` patches. Never call real external APIs in unit tests.
- **Test Setup:**
  - Always use the `db_session` fixture for database operations.
  - Tests must be marked with `@pytest.mark.asyncio`.
- **Naming Convention:** Test function names should be descriptive, starting with `test_` (e.g., `test_get_weather_success`).
