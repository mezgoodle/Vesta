# API Layer

This directory contains the FastAPI router configuration, endpoint definitions, and dependency injection logic.

## Structure

```text
api/
├── deps.py              # Dependency Injection
└── v1/
    ├── api.py           # Main router aggregator
    └── endpoints/       # Specific resource handlers
```

## Key Components

### [Dependency Injection (deps.py)](./deps.py)

Uses FastAPI's `Depends` system to decouple components and manage the request lifecycle.

- **`SessionDep`**: Provides a scoped async database session (`AsyncSession`) for each request.
- **`CurrentUser`**: Validates JWT bearer tokens or `X-API-Key` headers to fetch and inject the calling user context.
- **`CurrentSuperUser`**: Restricts endpoints to admin-level accounts.
- **`ADKServiceDep`**: Yields the ADK agent coordinator.
- **`KnowledgeServiceDep`**: Yields the LlamaIndex base RAG service.
- **`TTSServiceDep`**: Yields the Google TTS engine.
- **`OpenMeteoServiceDep`**: Yields the free OpenMeteo weather client.

### [API Router (./v1/api.py)](./v1/api.py)

Aggregates all endpoint routers into a single `api_router`. This is where the top-level routing structure is defined under the `/api/v1` namespace.

### Endpoints (./v1/endpoints/)

Each module in this directory corresponds to a specific resource or feature area:

- **`calendar.py`**: Connects to Google Calendar to schedule or update appointments.
- **`chat.py`**: Primary conversational gateway `/chat/process` connected to the ADK agent coordinator.
- **`devices.py`**: Connects to Home Assistant REST and WebSocket modules.
- **`google_auth.py`**: Handles Google Consent Screen redirection and callback flows.
- **`knowledge.py`**: Endpoint `/knowledge/sync` triggers background documentation ingestion from Google Drive.
- **`login.py`**: Generates and checks JWT access tokens.
- **`news.py`**: Registers or deletes news RSS subscriptions.
- **`sessions.py`**: Manages conversational history session CRUD and updates.
- **`tts.py`**: Exposes direct Text-To-Speech stream synthesis.
- **`users.py`**: Manages Telegram user onboarding, approvals, profiles, and permissions.
- **`weather.py`**: Serves city-based real-time weather and N-day geocoded forecasts via OpenMeteo.

## Versioning

The API uses a versioned structure (currently `v1`). All endpoints are prefixed with `/api/v1` in `app/main.py`. This allows for future breaking changes without disrupting existing clients.
