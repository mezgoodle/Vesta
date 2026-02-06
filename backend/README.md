# Vesta Backend

This is the backend service for the Vesta Smart Home Assistant, built with FastAPI. It provides a comprehensive API for managing smart home devices, calendar events, weather information, news subscriptions, and AI-powered chat interactions.

## Features

- 🏠 **Home Assistant Integration**: Control and monitor smart home devices
- 📅 **Google Calendar**: Manage calendar events with AI assistance
- 🌤️ **Weather Service**: Get current weather and forecasts via OpenWeatherMap
- 📰 **News Subscriptions**: Subscribe to and manage news feeds
- 💬 **AI Chat**: Conversational interface powered by OpenAI/Google AI
- 🔐 **User Authentication**: Secure JWT-based authentication
- 📊 **Database**: SQLite with SQLAlchemy ORM and Alembic migrations
- ⏰ **Task Scheduler**: Automated background tasks

## Prerequisites

- Python 3.8+
- pip
- SQLite (included with Python)

## Installation

1.  **Navigate to the backend directory:**

    ```bash
    cd backend
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**
    - **Windows:**
      ```powershell
      .\venv\Scripts\Activate
      ```
    - **macOS/Linux:**
      ```bash
      source venv/bin/activate
      ```

4.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **Set up environment variables:**

    Copy the `.env.example` file to a new file named `.env`:

    ```bash
    cp .env.example .env
    ```

    _Note: On Windows PowerShell, use `copy .env.example .env`_

2.  **Edit `.env`:**

    Open the `.env` file and fill in the required values:

    ```env
    # OpenAI Configuration
    OPENAI_API_KEY=your_openai_api_key

    # Home Assistant Configuration
    HOME_ASSISTANT_URL=http://homeassistant.local:8123
    HOME_ASSISTANT_TOKEN=your_long_lived_access_token

    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN=your_telegram_bot_token

    # Weather Service Configuration
    OPENWEATHER_API_KEY=your_openweathermap_api_key

    # Google Services Configuration
    GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
    GOOGLE_API_KEY=your_google_api_key
    GOOGLE_MODEL_NAME=gemini-pro
    ```

3.  **Database Setup:**

    Run Alembic migrations to set up the database:

    ```bash
    alembic upgrade head
    ```

## Running the Server

Start the development server using Uvicorn:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## API Documentation

Once the server is running, you can access the interactive API documentation at:

- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`

## Testing

Run the test suite using pytest:

```bash
pytest
```

For verbose output:

```bash
pytest -v
```

## API Endpoints

### Authentication

- `POST /api/v1/login/access-token` - Get access token

### Users

- `GET /api/v1/users/me` - Get current user
- `POST /api/v1/users/` - Create new user
- `GET /api/v1/users/` - List all users (admin)

### Calendar

- `GET /api/v1/calendar/events` - List calendar events
- `POST /api/v1/calendar/events` - Create calendar event
- `PUT /api/v1/calendar/events/{event_id}` - Update calendar event
- `DELETE /api/v1/calendar/events/{event_id}` - Delete calendar event

### Google Authentication

- `GET /api/v1/google-auth/authorize` - Initiate Google OAuth flow
- `GET /api/v1/google-auth/callback` - OAuth callback handler
- `GET /api/v1/google-auth/status` - Check authentication status

### Smart Devices

- `GET /api/v1/devices/` - List all devices
- `POST /api/v1/devices/{device_id}/control` - Control a device

### Weather

- `GET /api/v1/weather/current` - Get current weather

### News

- `GET /api/v1/news/subscriptions` - List news subscriptions
- `POST /api/v1/news/subscriptions` - Create news subscription
- `DELETE /api/v1/news/subscriptions/{subscription_id}` - Delete subscription

### Chat

- `POST /api/v1/chat/` - Send chat message
- `GET /api/v1/chat/history` - Get chat history

## Project Structure

```text
backend/
├── app/
│   ├── api/
│   │   ├── deps.py              # Dependency injection
│   │   └── v1/
│   │       ├── api.py           # API router aggregation
│   │       └── endpoints/       # API endpoint modules
│   │           ├── calendar.py
│   │           ├── chat.py
│   │           ├── devices.py
│   │           ├── google_auth.py
│   │           ├── login.py
│   │           ├── news.py
│   │           ├── users.py
│   │           └── weather.py
│   ├── core/
│   │   ├── config.py            # Application settings
│   │   ├── logger.py            # Logging configuration
│   │   ├── scheduler.py         # Background task scheduler
│   │   └── security.py          # Authentication utilities
│   ├── crud/                    # Database operations
│   ├── db/
│   │   └── session.py           # Database session management
│   ├── models/                  # SQLAlchemy models
│   ├── schemas/                 # Pydantic schemas
│   ├── services/                # Business logic
│   │   ├── google_auth.py
│   │   ├── google_calendar.py
│   │   ├── home.py
│   │   ├── llm.py
│   │   └── weather.py
│   ├── initial_data.py          # Database initialization
│   └── main.py                  # Application entry point
├── migrations/                  # Alembic database migrations
├── tests/                       # Test suite
├── alembic.ini                  # Alembic configuration
├── pyproject.toml               # Project metadata
├── requirements.txt             # Python dependencies
└── .env.example                 # Environment variables template
```

## Database Migrations

Create a new migration after model changes:

```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:

```bash
alembic upgrade head
```

Rollback last migration:

```bash
alembic downgrade -1
```

## License

MIT © [mezgoodle](https://github.com/mezgoodle)
