# Backend Services

This directory contains the core business logic, external API integrations, and AI agent coordinations for the Vesta backend.

## Services Overview

### [ADKService (adk_service.py)](./adk_service.py)

The central orchestrator of Vesta's conversational AI, replacing monolithic LLM clients. It coordinates the **Google ADK (Agent Development Kit)** multi-agent runtime.

*   **Key Responsibilities**:
    *   Synthesizing **request-scoped tools** bound to a specific database session and user ID.
    *   Constructing the agent delegation hierarchy: `VestaRootAgent` directing requests to `WeatherAgent`, `CalendarAgent`, and `KnowledgeAgent`.
    *   Running asynchronous execution loops via ADK's `InMemoryRunner` and streaming event logs.
    *   Capturing final text streams and logging tool invocations/agent transfers directly to Google Cloud Logging.

### [ChatManager (chat_manager.py)](./chat_manager.py)

Manages conversational history rolling windows and asynchronously triggers rolling session summary updates.

*   **Key Responsibilities**:
    *   Evaluating conversation size against limits (triggers summary updates every 10 messages).
    *   Offloading summary generation tasks to a background thread transport using `SummaryAgent`.

### [KnowledgeService (knowledge.py)](./knowledge.py)

Implements high-performance Retrieval-Augmented Generation (RAG) for Vesta.

*   **Key Responsibilities**:
    *   Integrating with LlamaIndex and a local **ChromaDB Vector Store** (`./chroma_db`).
    *   Using LlamaCloud/LlamaParse to extract details from complex Google Drive documents.
    *   Providing contextual query engines for the `KnowledgeAgent` to consult when answering user prompts.

### [GoogleTTSService (google_tts.py)](./google_tts.py)

Exposes audio generation capabilities.

*   **Key Responsibilities**:
    *   Connecting to the `google-cloud-texttospeech` API.
    *   Synthesizing assistant text responses into highly compressed `OGG_OPUS` formats optimized for quick mobile transmission on Telegram.

### [OpenMeteoService (open_meteo_service.py)](./open_meteo_service.py)

The primary weather service client in Vesta.

*   **Key Responsibilities**:
    *   Resolving query city names into precise Latitude/Longitude degrees using OpenMeteo's Geocoding API.
    *   Fetching weather forecast parameters (max/min temps, rain probability) without requiring proprietary API tokens.

### [GoogleCalendarService (google_calendar.py)](./google_calendar.py)

Coordinates calendar synchronization.

*   **Key Responsibilities**:
    *   Authenticating with the Google Calendar API using stored OAuth refresh credentials.
    *   Listing upcoming events, creating new entries, or modifying existing schedules.

### [HomeAssistantService (home.py)](./home.py)

Serves as the REST and WebSocket bridge to your home automation server.

*   **Key Responsibilities**:
    *   Reading device states (lights, switches, climate control).
    *   Dispatching service commands to control entities.

### [GoogleAuthService (google_auth.py)](./google_auth.py)

Manages the OAuth 2.0 flow with Google APIs, securely storing user refresh credentials.

---

## Agent Orchestration Flow

```text
User Request → [ADKService] → [VestaRootAgent]
                                 │
                 ┌───────────────┼───────────────┐
                 ▼               ▼               ▼
           [WeatherAgent] [CalendarAgent] [KnowledgeAgent]
                 │               │               │
                 ▼               ▼               ▼
          [OpenMeteo]      [Google Cal]      [ChromaDB]
```

1.  A message from the user (e.g. "What is on my calendar today?") is submitted via `/chat/process`.
2.  `ADKService` creates tools bound to the current database session.
3.  The agent pipeline starts. `VestaRootAgent` evaluates the prompt, identifies it requires scheduling access, and delegates execution control to `CalendarAgent`.
4.  `CalendarAgent` calls the request-scoped calendar tools (connected to `GoogleCalendarService`).
5.  Results are returned to the root agent, which generates the final response text.
