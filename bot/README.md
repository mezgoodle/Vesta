# Vesta Telegram Bot

This is the Telegram bot interface for the Vesta Smart Home Assistant. It provides a conversational interface to interact with your smart home, manage calendar events, check weather, and more through Telegram.

## Features

- 🤖 **Conversational AI**: Natural language interaction with your smart home
- 🏠 **Device Control**: Control Home Assistant devices via chat
- 📅 **Calendar Management**: View and create calendar events
- 🌤️ **Weather Updates**: Get current weather information
- 📰 **News Feeds**: Subscribe to and read news
- 🔐 **User Authentication**: Secure access control with user approval system
- 🎯 **Rich UI**: Interactive keyboards and inline buttons
- ⚡ **Middleware**: Throttling, ACL, and logging

## Prerequisites

- Python 3.8+
- pip
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Access to Vesta Backend API

## Installation

1. **Navigate to the bot directory:**

   ```bash
   cd bot
   ```

2. **Create a virtual environment (recommended):**

   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment:**
   - **Windows:**
     ```powershell
     .\.venv\Scripts\Activate
     ```
   - **macOS/Linux:**
     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. **Set up environment variables:**

   Create a `.env` file in the bot directory:

   ```env
   BOT_TOKEN=your_telegram_bot_token
   BACKEND_API_KEY=your_backend_api_key
   ```

   - Get your `BOT_TOKEN` from [@BotFather](https://t.me/botfather)
   - The `BACKEND_API_KEY` should match the key configured in your Vesta backend

2. **Configure bot settings:**

   Edit `tgbot/config.py` if you need to customize:
   - Admin user IDs
   - Backend API URL
   - Other bot-specific settings

## Running the Bot

Start the bot:

```bash
python bot.py
```

The bot will start polling for updates and respond to user messages.

## Bot Commands

- `/start` - Start the bot and show welcome message
- `/help` - Show available commands
- `/menu` - Show main menu with quick actions
- `/weather` - Get current weather
- `/calendar` - View calendar events
- `/devices` - List and control smart devices
- `/news` - Manage news subscriptions

## Project Structure

```text
bot/
├── tgbot/
│   ├── config.py                # Bot configuration
│   ├── filters/                 # Custom message filters
│   ├── handlers/                # Message and callback handlers
│   │   ├── admin.py
│   │   ├── calendar.py
│   │   ├── chat.py
│   │   ├── devices.py
│   │   ├── news.py
│   │   ├── start.py
│   │   └── weather.py
│   ├── infrastructure/          # Core infrastructure
│   │   ├── logger.py            # Logging setup
│   │   └── user_service.py      # User management
│   ├── keyboards/               # Reply and inline keyboards
│   │   ├── inline.py
│   │   └── reply.py
│   ├── middlewares/             # Bot middlewares
│   │   ├── acl.py               # Access control
│   │   ├── logging.py           # Request logging
│   │   ├── settings.py          # Settings injection
│   │   └── throttling.py        # Rate limiting
│   ├── services/                # External service integrations
│   │   ├── admins_notify.py
│   │   ├── setting_commands.py
│   │   └── user_cache.py
│   └── states/                  # FSM states for conversations
├── bot.py                       # Main bot entry point
├── loader.py                    # Bot and dispatcher initialization
├── requirements.txt             # Python dependencies
└── .env                         # Environment variables
```

## User Access Control

The bot implements an access control system:

1. **First-time users**: When a user starts the bot, they are added to the database with `is_approved=False`
2. **Admin approval**: Admins receive notifications about new users and can approve them
3. **Approved users**: Only approved users can access bot features

To approve users, admins can use the admin panel accessible through the bot interface.

## Logging

The bot uses structured logging configured in `logger_sa.json`. Logs include:

- User interactions
- Command executions
- API calls to backend
- Error tracking

## Middlewares

The bot uses several middlewares for enhanced functionality:

- **ACLMiddleware**: Ensures only approved users can access the bot
- **ThrottlingMiddleware**: Prevents spam and rate-limits requests
- **LoggingMiddleware**: Logs all incoming messages and callbacks
- **ConfigMiddleware**: Injects configuration into handlers

## Development

### Adding New Handlers

1. Create a new handler file in `tgbot/handlers/`
2. Define your handler functions
3. Import the handlers in `tgbot/handlers/__init__.py`
4. The handlers will be automatically registered on startup

### Adding New Keyboards

1. Create keyboard functions in `tgbot/keyboards/`
2. Use `InlineKeyboardBuilder` for inline keyboards
3. Use `ReplyKeyboardBuilder` for reply keyboards

## Links

- [AIOgram Documentation](https://docs.aiogram.dev/en/latest/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Vesta Backend](../backend/README.md)

## Contribute

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

MIT © [mezgoodle](https://github.com/mezgoodle)
