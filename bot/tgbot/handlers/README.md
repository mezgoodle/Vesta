# Telegram Bot Handlers

This directory contains the event handlers that respond to user messages, commands, and callback queries.

## Organization

Handlers are organized by feature area to keep the code modular and maintainable.

### Key Handlers

- **[admin.py](file:///c:/Projects/Vesta/bot/tgbot/handlers/admin.py)**: Commands restricted to bot administrators (e.g., user approval, system status).
- **[start.py](file:///c:/Projects/Vesta/bot/tgbot/handlers/start.py)**: Handles the `/start` command, user registration, and initial onboarding.
- **[chat.py](file:///c:/Projects/Vesta/bot/tgbot/handlers/chat.py)**: Processes general text messages using the LLM service for conversational responses.
- **[devices.py](file:///c:/Projects/Vesta/bot/tgbot/handlers/devices.py)**: Control logic for smart home devices (listing, toggling state).
- **[weather.py](file:///c:/Projects/Vesta/bot/tgbot/handlers/weather.py)**: Handles weather inquiries.
- **[calendar.py](file:///c:/Projects/Vesta/bot/tgbot/handlers/calendar.py)**: Calendar event viewing and creation flows.
- **[news.py](file:///c:/Projects/Vesta/bot/tgbot/handlers/news.py)**: News subscription management and feed viewing.

## Handler Registration

Handlers are registered in the `__init__.py` or main bot setup using `aiogram` Routers.
Example pattern:

```python
# In handlers/my_feature.py
router = Router()

@router.message(Command("feature"))
async def my_feature_handler(message: Message):
    ...

# In bot.py
dp.include_router(my_feature.router)
```

## State Management

Complex interactions (like creating a calendar event) use **FSM (Finite State Machine)**. States are defined in `tgbot/states/`. Handlers inside `handlers/` transition users between these states to collect multi-step input.
