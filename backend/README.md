# Vesta Backend Service

This is the backend service for the Vesta Smart Home Assistant, built with FastAPI. It provides a robust, high-performance API for managing smart home devices, calendar events, weather information, news subscriptions, and AI-powered interactions.

---

## 🚀 Key Features

*   🏠 **Home Assistant Integration**: Secure control and monitoring of home smart devices.
*   📅 **Google Calendar**: Bi-directional event management using advanced natural language processing.
*   🌤️ **Weather Service**: Location-aware current conditions and daily forecasts retrieved via the open-source OpenMeteo API.
*   🎙️ **Google TTS Engine**: Synthesizes assistant conversational responses into OGG/OPUS audio streams.
*   📚 **RAG Integration**: Document searching and retrieval via LlamaIndex, synced directly from Google Drive folders into a local Chroma vector database.
*   💬 **Conversational AI**: Advanced multi-agent orchestration powered by the **Google ADK (Agent Development Kit)** framework and Google Gemini.
*   🔐 **Multi-tiered Authentication**: Secure JWT-based user authentication and token-based service-to-service validation.
*   📊 **Database Layer**: Robust SQLAlchemy 2.0 ORM over asynchronous PostgreSQL (fully compatible with Supabase).
*   ⏰ **Task Scheduler**: Periodic background tasks orchestrated by APScheduler.

---

## 📋 Prerequisites

*   Python 3.13+
*   PostgreSQL Database (Supabase recommended; standard SQL pooling is supported)
*   Google Cloud Service Account (for TTS and logging)
*   Google APIs Client credentials (for Calendar OAuth integration)
*   LlamaCloud/LlamaParse account keys (for RAG parsing)

---

## 🛠️ Installation

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    ```

3.  **Activate the virtual environment:**
    *   **Windows (PowerShell):**
        ```powershell
        .\.venv\Scripts\Activate
        ```
    *   **macOS/Linux:**
        ```bash
        source .venv/bin/activate
        ```

4.  **Install dependencies:**
    Use `uv` (recommended) or standard `pip`:
    ```bash
    pip install -r requirements.txt
    ```

---

## ⚙️ Configuration

1.  **Set up environment variables:**
    Copy the `.env.example` file to a new file named `.env`:
    ```bash
    cp .env.example .env
    ```
    *(On Windows PowerShell, use `copy .env.example .env`)*

2.  **Fill in `.env` settings:**
    Open `.env` and fill in the required keys:

    ```env
    # --- Database Configuration ---
    # Asynchronous PostgreSQL (compatible with Supabase Pooler)
    DATABASE_URL=postgresql+asyncpg://postgres.your-project-ref:your-password@aws-0-eu-west-1.pooler.supabase.com:6543/postgres?prepared_statement_cache_size=0

    # --- Home Assistant ---
    HOME_ASSISTANT_URL=http://homeassistant.local:8123
    HOME_ASSISTANT_TOKEN=your_long_lived_access_token

    # --- Telegram ---
    TELEGRAM_BOT_TOKEN=your_telegram_bot_token

    # --- Weather Service ---
    # OpenWeatherMap key (optional legacy or custom helper scripts)
    OPENWEATHER_API_KEY=your_openweathermap_api_key

    # --- Google Cloud & Gemini AI ---
    GOOGLE_APPLICATION_CREDENTIALS=path/to/logger_sa.json
    GOOGLE_API_KEY=your_google_api_key
    GOOGLE_MODEL_NAME=gemini-3-flash-preview  # Recommended ADK Model

    # --- Google Calendar OAuth ---
    GOOGLE_CLIENT_ID=your_google_oauth_client_id
    GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret
    GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/google-auth/callback

    # --- LlamaIndex RAG & Knowledge Base ---
    LLAMA_PARSE_API_KEY=your_llamacloud_api_key
    GOOGLE_DRIVE_FOLDER_ID=your_google_drive_folder_id
    CHROMA_DB_PATH=./chroma_db
    ```

3.  **Run Database Migrations:**
    Initialize your PostgreSQL schemas via Alembic:
    ```bash
    alembic upgrade head
    ```

---

## 🏃 Running the Server

Start the FastAPI application using Uvicorn:
```bash
uvicorn app.main:app --reload
```
The server will boot up and be accessible locally at `http://127.0.0.1:8000`.

### API Documentation
FastAPI automatically generates interactive document endpoints. With the server running, visit:
*   **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
*   **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🤖 Google ADK Multi-Agent Architecture

Vesta Backend replaces traditional, monolithic LLM routers with a sophisticated, conversational Multi-Agent orchestrator powered by the **Google ADK (Agent Development Kit)**.

### 1. Agent Hierarchy

```text
VestaRootAgent (Dispatcher)
  ├── WeatherAgent
  ├── CalendarAgent
  └── KnowledgeAgent
```

*   **VestaRootAgent**: The primary conversational interface. Acts as a supervisor that evaluates natural language intent. It uses ADK's **Agent Transfer** mechanism to hand over control to specialized sub-agents based on their descriptions. For casual chit-chat, the Root Agent replies directly.
*   **WeatherAgent**: Possesses tools to coordinate city geocoding and query current conditions or forecasts via OpenMeteo.
*   **CalendarAgent**: Possesses tools to authenticate calendar flows, fetch schedules, and dynamically create, edit, or delete events.
*   **KnowledgeAgent**: Connected to the local RAG engine. Possesses tools to search internal documentation synchronized from Google Drive.
*   **SummaryAgent** *(Standalone)*: Used asynchronously by background tasks to evaluate and generate rolling conversation session summaries.

### 2. Request-Scoped Tools

All tool closures (defined in `app/services/gemini_tools.py`) are created on a **per-request basis** and bound specifically to the calling `user_id` and the current `AsyncSession` database transaction. This enforces strict sandboxing, preventing data leaks between distinct users.

---

## 📡 API Endpoints

### 🔑 Authentication & Login
*   `POST /api/v1/login/access-token` - Retrieve a JWT bearer token.

### 👤 User Management
*   `GET /api/v1/users/` - List all users (restricted to Admin superusers).
*   `POST /api/v1/users/` - Create a new Telegram user record.
*   `GET /api/v1/users/allowed/telegram-ids` - Fetch IDs of approved users (used by Bot Cache).
*   `GET /api/v1/users/telegram/{telegram_id}` - Retrieve user info by Telegram ID.
*   `PATCH /api/v1/users/telegram/{telegram_id}/approval` - Approve/disapprove a user (restricted to Admins).
*   `GET /api/v1/users/{user_id}` - Get user details by database ID.
*   `PATCH /api/v1/users/{user_id}` - Update user settings (e.g. daily summaries, city name).
*   `DELETE /api/v1/users/{user_id}` - Delete a user from the system.

### 💬 Conversational AI & Sessions
*   `POST /api/v1/chat/process` - Submit a prompt to the Google ADK multi-agent orchestrator. Supports `want_voice` to return raw synthesized OGG TTS.
*   `GET /api/v1/chat/` - Retrieve chat message history records.
*   `POST /api/v1/chat/` - Log a manual chat event.
*   `DELETE /api/v1/chat/{chat_id}` - Delete a logged chat record.
*   `GET /api/v1/sessions/` - Retrieve active chat sessions.
*   `POST /api/v1/sessions/` - Create a new chat session.
*   `GET /api/v1/sessions/{session_id}` - Fetch a specific session along with its rolling summary.
*   `PATCH /api/v1/sessions/{session_id}` - Update a session's title or attributes.
*   `DELETE /api/v1/sessions/{session_id}` - Terminate a session.

### 📅 Smart Calendar
*   `GET /api/v1/calendar/events` - Retrieve calendar events.
*   `POST /api/v1/calendar/events` - Create a calendar event.
*   `PUT /api/v1/calendar/events/{event_id}` - Update a calendar event.
*   `DELETE /api/v1/calendar/events/{event_id}` - Remove a calendar event.

### 🔑 Google OAuth Integration
*   `GET /api/v1/google-auth/authorize` - Retrieve the Google Consent Screen redirect URL.
*   `GET /api/v1/google-auth/callback` - OAuth 2.0 redirection flow callback handler.
*   `GET /api/v1/google-auth/status` - Validate current Google API token storage status.

### 🏡 Smart Devices
*   `GET /api/v1/devices/` - List registered Home Assistant entities.
*   `POST /api/v1/devices/{device_id}/control` - Control device power state or options.

### 🌤️ Weather Forecast
*   `GET /api/v1/weather/current` - Get real-time weather and N-day forecasts via OpenMeteo.

### 🎙️ Text-To-Speech (TTS)
*   `POST /api/v1/tts/synthesize` - Convert textual inputs directly into OGG/OPUS voice streams.

### 📚 Knowledge Base (RAG)
*   `POST /api/v1/knowledge/sync` - Trigger a background sync task of Google Drive files to ChromaDB.

---

## 🧪 Testing

The backend includes a comprehensive, automated test suite utilizing `pytest` and an ephemeral in-memory SQLite database (`aiosqlite`) to guarantee isolated testing.

To execute the test suite:
```bash
pytest
```
To run tests with full verbose logs:
```bash
pytest -v
```

---

## 📂 Project Structure

```text
backend/
├── app/
│   ├── agents/                 # Google ADK Agent configurations
│   │   ├── calendar_agent.py   # ADK interface for Calendar
│   │   ├── knowledge_agent.py  # ADK interface for RAG
│   │   ├── root_agent.py       # Main ADK routing agent
│   │   ├── summary_agent.py    # Generates session context summaries
│   │   └── weather_agent.py    # ADK interface for Weather
│   ├── api/
│   │   ├── deps.py             # Dependency injections & authentication
│   │   └── v1/
│   │       ├── api.py          # Routing aggregator
│   │       └── endpoints/      # Resource endpoint files (chat, tts, weather...)
│   ├── core/
│   │   ├── config.py           # Application Settings (Pydantic-Settings)
│   │   ├── logger.py           # Structured logging setup (GCP support)
│   │   ├── scheduler.py        # Periodic background tasks (APScheduler)
│   │   └── security.py         # Passwords & JWT tokens
│   ├── crud/                   # Core database queries
│   ├── db/
│   │   └── session.py          # Session generation factory
│   ├── models/                 # SQLAlchemy 2.0 ORM schemas
│   ├── schemas/                # Pydantic validation structures
│   ├── services/               # Core business services
│   │   ├── adk_service.py      # Main Google ADK agent coordinator
│   │   ├── chat_manager.py     # Rolling summaries generator
│   │   ├── gemini_tools.py     # Gemini request-scoped tool definitions
│   │   ├── google_auth.py      # Google OAuth refresh credentials
│   │   ├── google_calendar.py  # Google Calendar API wrapper
│   │   ├── google_tts.py       # Google Cloud TTS engine client
│   │   ├── home.py             # Home Assistant REST connector
│   │   ├── knowledge.py        # LlamaIndex Drive & Chroma database sync
│   │   └── weather.py          # Legacy OpenWeatherMap client
│   ├── initial_data.py         # Superuser creation
│   └── main.py                 # FastAPI Application Entrypoint
├── migrations/                 # Alembic Database Migration scripts
├── tests/                      # Pytest Suite
├── alembic.ini                 # Alembic configuration
├── pyproject.toml              # Project dependencies & tool setups
└── requirements.txt            # Transformed requirements file
```

---

## 📄 License

MIT © [mezgoodle](https://github.com/mezgoodle)
