# Vesta Telegram Bot

This is the interactive Telegram bot interface for the Vesta Smart Home Assistant, built with the modern **AIOgram 3.x** async framework. It acts as the primary user-facing touchpoint, providing a premium, conversational interface to control your smart home, manage schedules, fetch geocoded weather forecasts, search internal documents, and more.

---

## 🚀 Key Features

*   🤖 **Conversational AI Interface**: Fluid natural language chat with Vesta, powered by the backend's Google ADK multi-agent orchestrator.
*   🎙️ **Voice Messaging Support**: Integrated Speech-To-Text (STT) and Text-To-Speech (TTS) streams allow users to chat using standard Telegram voice notes.
*   📅 **Schedule Manager**: Interactive command shortcuts (`/today`, `/upcoming`) to check and track calendar events.
*   🌤️ **Geocoded Forecasts**: Dedicated `/weather` command supporting city geocoding and N-day detailed forecast layouts.
*   🔐 **Granular Access Control**: Seamless, secure onboarding workflow utilizing router-level authorization filters and centralized database checks.
*   💬 **Session Management**: Full support to save, switch, rename, or delete distinct chat sessions using intuitive inline keyboards.
*   🍔 **Interactive Extras**: Dynamic features like `/food` matching user parameters to a fun recommendation process.

---

## 📋 Prerequisites

*   Python 3.13+
*   A Telegram Bot Token (obtained from [@BotFather](https://t.me/botfather))
*   A running Vesta Backend service instance

---

## 🛠️ Installation

1.  **Navigate to the bot directory:**
    ```bash
    cd bot
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
    Use `pip` to install requirements:
    ```bash
    pip install -r requirements.txt
    ```

---

## ⚙️ Configuration

Create a `.env` file inside the `/bot` directory:

```env
BOT_TOKEN=your_telegram_bot_token
BACKEND_API_KEY=your_backend_api_key_here
```

*   **`BOT_TOKEN`**: The unique API token supplied by [@BotFather](https://t.me/botfather).
*   **`BACKEND_API_KEY`**: Must match the `BACKEND_API_KEY` string configured in the Vesta backend's `.env`. This is transmitted in the `X-API-Key` header for secure service-to-service calls.

---

## 🏃 Running the Bot

Start the bot client:
```bash
python bot.py
```
On startup, the bot initializes its local approved user cache, sets command autocomplete parameters, and begins async polling for updates.

---

## 📡 Bot Commands

*   `/start` - Initialize contact. Checks approval and initiates admin request forms for new users.
*   `/help` - View descriptions of all active bot commands.
*   `/new` - Create and switch to a brand new conversational chat session.
*   `/chats` - Open an inline keyboard list of your saved chat sessions (allows switching, renaming, or deleting).
*   `/today` - Quickly fetch today's calendar event details.
*   `/upcoming` - View a list of upcoming Google Calendar appointments.
*   `/weather [city] [days]` - Query geocoded temperature and precipitation forecasts via OpenMeteo (e.g. `/weather London 3`).
*   `/food` - Start a fun, interactive food recommendation helper.
*   `/info` - Retrieve your personal profile card containing Telegram details and backend sync status.
*   `/google_auth` - Retrieve your custom authorization URL to connect Vesta to your Google Calendar.
*   `/enable_daily_summary` - Opt-in to receive automatic morning briefing notifications.
*   `/admin` - Admin panel dashboard (restricted to administrators) to review, approve, or reject new user access requests.
*   `/reset` - Clean the current conversational state and session pointers.

---

## 🔐 User Access Control

Vesta Bot utilizes a secure, cache-accelerated authorization model:

1.  **First-time Connection**: When a user runs `/start`, their credentials are sent to the backend as `is_allowed=False`. The bot notifies the configured Admin with an inline menu (`permissions_markup`) to approve or reject the applicant.
2.  **Access Verification**: Rather than calling the REST API on every message, access is validated at the router level via `IsApprovedUserFilter` and matched against a local, memory-cached list of approved Telegram IDs (`UserCache`).
3.  **Synchronization**: The `UserCache` singleton is pre-loaded on bot startup by querying `/users/allowed/telegram-ids` and updated dynamically during admin approval calls.
4.  *Note: The legacy `ACLMiddleware` is maintained in `tgbot/middlewares/acl.py` but is disabled in `bot.py` in favor of cleaner, router-level filter checking.*

---

## 📂 Project Structure

```text
bot/
├── tgbot/
│   ├── config.py                # Pydantic Configuration loader
│   ├── filters/                 # Request validation filters
│   │   └── approved_user.py     # IsApprovedUserFilter validator
│   ├── handlers/                # AIOgram Command/Event routers
│   │   ├── admin.py             # User approval & administrative tools
│   │   ├── calendar.py          # Calendar shortcuts (/today, /upcoming)
│   │   ├── echo.py              # Start, photo helpers, and fallback copier
│   │   ├── errors.py            # Global bot error boundary logs
│   │   ├── food.py              # Food recommendation game engine
│   │   ├── help.py              # Interactive help card
│   │   ├── llm.py               # Conversational AI & Voice gateway (/new, /reset)
│   │   ├── sessions.py          # Chat session manager menu (/chats)
│   │   ├── state.py             # Basic state handlers
│   │   ├── user.py              # User settings & google auth triggers
│   │   ├── user_update.py       # Inline callbacks for profile settings
│   │   └── weather.py           # Geocoded weather queries (/weather)
│   ├── infrastructure/          # OOP HTTP Clients (wraps backend API)
│   │   ├── ARCHITECTURE.md      # OOP Design pattern guide
│   │   ├── README.md            # Client integration docs & schemas
│   │   ├── base_service.py      # Abstract Base Client (aiohttp wrapper)
│   │   ├── calendar_service.py  # REST client for backend Calendar
│   │   ├── llm_service.py       # REST client for backend ADK Chat
│   │   ├── logger.py            # Custom logging setup
│   │   ├── tts_service.py       # REST client for backend TTS Synthesis
│   │   ├── user_service.py      # REST client for backend Users
│   │   └── weather_service.py   # REST client for backend Weather
│   ├── keyboards/               # Keyboard templates & factory builders
│   │   ├── inline/              # Inline callback menus
│   │   └── reply/               # Custom keyboard inputs
│   ├── middlewares/             # Update pipeline middlewares
│   │   ├── acl.py               # Access control (legacy)
│   │   ├── logging.py           # Structured traffic logging
│   │   ├── settings.py          # Configuration context injector
│   │   └── throttling.py        # Throttling & anti-spam rate limiter
│   ├── services/                # Standalone bot business services
│   │   ├── admins_notify.py     # System alert broadcasts
│   │   ├── setting_commands.py  # Autocomplete command registers
│   │   ├── stt.py               # Google Cloud STT speech transcriber
│   │   ├── user_cache.py        # Scoped memory cache of allowed IDs
│   │   └── utils.py             # Message rendering and formatting helpers
│   └── states/                  # Finite State Machine definitions
├── bot.py                       # Main Bot Startup script
├── loader.py                    # Dispatcher & client instance loaders
└── requirements.txt             # Bot dependencies file
```

---

## 🎙️ Voice & Audio Flow

Vesta Bot supports dynamic voice chats. When a user submits a voice message:
1.  `llm.py` catches the voice update and downloads the audio bytes.
2.  The audio is transcribed to text using `stt.py` (STT service).
3.  The text prompt is transmitted to the backend via `llm_service.py` with `want_voice=True`.
4.  The backend processes the prompt through the ADK agent, synthesizes an OGG/OPUS response audio clip via Google Cloud TTS, and returns it as a Base64-encoded string.
5.  The bot decodes the base64 string, loads it into a `BufferedInputFile`, and transmits it back to the user via Telegram's `.answer_voice()` command.

---

## 📄 License

This bot interface is licensed under the MIT License. See [LICENSE](../LICENSE) for details.
