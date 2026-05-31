# Vesta: Smart AI-Powered Home Assistant

Vesta is a state-of-the-art, AI-driven Smart Home Assistant monorepo consisting of a robust **FastAPI backend** and an interactive **Telegram Bot interface**. Powered by **Google Gemini** and orchestrated via the **Google ADK multi-agent framework**, Vesta acts as the intelligent brain of your living space.

---

## 🚀 Key Features

*   💬 **Conversational AI**: Multi-agent natural language understanding (NLU) powered by Gemini.
*   🏠 **Home Assistant Integration**: Secure, voice- and text-guided smart device listing, monitoring, and control.
*   📅 **Calendar Assistant**: Deep integration with Google Calendar to list, schedule, edit, or delete events using natural language.
*   🌤️ **Smart Weather Forecasts**: Location-aware current conditions and daily forecasts retrieved via the open-source OpenMeteo API.
*   🎙️ **Voice Interactions**: Out-of-the-box support for Speech-To-Text (STT) and Google Text-To-Speech (TTS) for hands-free voice message chats.
*   📚 **RAG Knowledge Base**: High-performance Retrieval-Augmented Generation using LlamaIndex and a local ChromaDB, synchronizing documents directly from Google Drive.
*   🔐 **Secure Onboarding**: Administrator approval flow with localized Telegram caches and API-key/JWT authorization.

---

## 📐 System Architecture

Vesta is structured as a modular monorepo. Here is how the systems connect and exchange details:

```mermaid
graph TD
    User([Telegram User]) <-->|Text / Voice Messages| Bot[Telegram Bot (aiogram)]
    Bot <-->|REST API + JWT/API-Keys| Backend[FastAPI Backend]
    
    subgraph FastAPI Backend App
        Backend <--> deps[Dependency Injection]
        deps <--> ADK[ADK Service Agent Runner]
        
        subgraph Multi-Agent System (Google ADK)
            ADK --> RootAgent[Root Dispatcher Agent]
            RootAgent --> WeatherAgent[Weather Agent]
            RootAgent --> CalendarAgent[Calendar Agent]
            RootAgent --> KnowledgeAgent[Knowledge Agent]
        end
        
        WeatherAgent <--> OpenMeteo[OpenMeteo API]
        CalendarAgent <--> GoogleCal[Google Calendar API]
        KnowledgeAgent <--> Chroma[(ChromaDB Vector Store)]
        Chroma <--> LlamaIndex[LlamaIndex + Google Drive Sync]
        
        ADK <--> DB[(Supabase PostgreSQL)]
    end
```

---

## 📂 Repository Structure

```text
Vesta/
├── backend/                # FastAPI Application
│   ├── app/
│   │   ├── agents/         # Google ADK agent configurations
│   │   ├── api/            # API endpoints & dependency injection
│   │   ├── core/           # Configuration, logging & scheduler
│   │   ├── crud/           # Database operations
│   │   ├── db/             # Database session configurations
│   │   ├── models/         # SQLAlchemy 2.0 ORM schemas
│   │   ├── schemas/        # Pydantic validation schemas
│   │   ├── services/       # Core business logic (ADK, RAG, TTS, Home)
│   │   └── main.py         # Backend startup script
│   ├── migrations/         # Alembic database migrations
│   └── tests/              # Automated pytest suite
│
├── bot/                    # Telegram Bot Application
│   ├── tgbot/
│   │   ├── filters/        # Custom message filters (e.g. IsApprovedUserFilter)
│   │   ├── handlers/       # Command & event handlers (admin, calendar, llm, weather)
│   │   ├── infrastructure/ # OOP HTTP Service clients (BaseAPIService wrappers)
│   │   ├── keyboards/      # Dynamic reply & inline menus
│   │   ├── middlewares/    # Request/response hook pipelines
│   │   ├── services/       # STT, caching, notification routines
│   │   └── states/         # FSM structures
│   └── bot.py              # Telegram bot entry point
```

---

## 🛠️ Quick Start

Detailed instructions can be found inside the respective service directories:

### 1. Backend Setup
1.  Navigate to `/backend`.
2.  Set up your Python virtual environment:
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Configure `.env` using `.env.example`.
5.  Run Alembic database upgrades:
    ```bash
    alembic upgrade head
    ```
6.  Start the development server:
    ```bash
    uvicorn app.main:app --reload
    ```
    *Access Swagger UI at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)*.

### 2. Bot Setup
1.  Navigate to `/bot`.
2.  Create your Python virtual environment:
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Configure your token credentials in `.env`.
5.  Start the polling client:
    ```bash
    python bot.py
    ```

---

## 📖 Sub-project Documentation

For in-depth explanations on features, configurations, and internal mechanisms, see:
*   📚 **[Backend Documentation](./backend/README.md)**
*   🤖 **[Telegram Bot Documentation](./bot/README.md)**
*   📐 **[Infrastructure Architecture](./bot/tgbot/infrastructure/ARCHITECTURE.md)**

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.