# Backend Services

This directory contains the core business logic and external service integrations for the Vesta backend.

## Services Overview

### [GoogleAuthService](file:///c:/Projects/Vesta/backend/app/services/google_auth.py)

Handles the OAuth 2.0 authentication flow with Google APIs.

- **Key Responsibilities**:
  - Generating authorization URLs
  - Exchanging authorization codes for credentials
  - Refreshing access tokens
  - Storing and retrieving user credentials from the database

### [GoogleCalendarService](file:///c:/Projects/Vesta/backend/app/services/google_calendar.py)

Manages interactions with the Google Calendar API.

- **Key Responsibilities**:
  - Listing upcoming events
  - Creating new events
  - Parsing natural language time references (via LLM helper or direct parsing)
  - Formatting events for user display

### [HomeAssistantService](file:///c:/Projects/Vesta/backend/app/services/home.py)

Acts as the bridge between Vesta and your Home Assistant instance.

- **Key Responsibilities**:
  - Fetching entity states
  - Controlling devices (turn on/off, set values)
  - interfacing with the Home Assistant REST API and WebSocket API

### [LLMService](file:///c:/Projects/Vesta/backend/app/services/llm.py)

Powered by OpenAI or Google Gemini, this service processes natural language user inputs.

- **Key Responsibilities**:
  - Understanding user intent (Command classification)
  - Generating conversational responses
  - Extracting structured data from natural language (e.g., for calendar events)
  - Reasoning about device states and weather

### [WeatherService](file:///c:/Projects/Vesta/backend/app/services/weather.py)

Integrates with OpenWeatherMap to provide real-time weather data.

- **Key Responsibilities**:
  - Fetching current weather conditions
  - Getting forecasts
  - Providing weather summaries for the dashboard or chat

## Service Interaction Flow

The `LLMService` often acts as an orchestrator:

1.  User sends a message (e.g., "Turn on the lights").
2.  `LLMService` analyzes the intent.
3.  If a device command is detected, it delegates to `HomeAssistantService`.
4.  The result is fed back to `LLMService` to generate a confirmation response.
