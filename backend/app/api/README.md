# API Layer

This directory contains the FastAPI router configuration, endpoint definitions, and dependency injection logic.

## Structure

```
api/
├── deps.py              # Dependency Injection
└── v1/
    ├── api.py           # Main router aggregator
    └── endpoints/       # Specific resource handlers
```

## Key Components

### [Dependency Injection (deps.py)](file:///c:/Projects/Vesta/backend/app/api/deps.py)

Uses FastAPI's `Depends` system to decouple components and manage request lifecycle.

- **`get_db`**: Provides a database session for each request.
- **`get_current_user`**: Validates JWT tokens and returns the authenticated user context.
- **`get_current_active_superuser`**: Ensures the user has admin privileges.

### [API Router (v1/api.py)](file:///c:/Projects/Vesta/backend/app/api/v1/api.py)

Aggregates all endpoint routers into a single `api_router`. This is where the top-level routing structure is defined (e.g., `/users`, `/calendar`).

### Endpoints (v1/endpoints/)

Each module in this directory corresponds to a resource or feature area:

- **`calendar.py`**: Calendar management endpoints.
- **`chat.py`**: Chat interface endpoints.
- **`devices.py`**: Smart home device control.
- **`google_auth.py`**: Google OAuth callback handlers.
- **`login.py`**: User authentication and token generation.
- **`users.py`**: User account management.
- **`weather.py`**: Weather data endpoints.

## Versioning

The API uses a versioned structure (currently `v1`). All endpoints are prefixed with `/api/v1` in `app/main.py`. This allows for future breaking changes without disrupting existing clients.
