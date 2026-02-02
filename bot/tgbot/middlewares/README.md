# Bot Middlewares

Middlewares wraps the update processing pipeline, allowing you to execute code before and after a handler is called.

## Available Middlewares

### [ACLMiddleware (acl.py)](file:///c:/Projects/Vesta/bot/tgbot/middlewares/acl.py)

**Access Control List**. This is critical for security.

- Checks if the user exists in the local database.
- Verifies if the user is `approved` by an admin.
- Blocks access to unauthorized users and prompts them to wait for approval.

### [LoggingMiddleware (logging.py)](file:///c:/Projects/Vesta/bot/tgbot/middlewares/logging.py)

Provides visibility into bot traffic.

- Logs incoming messages with user details.
- Logs callback queries (button clicks).
- Helpful for debugging and auditing usage.

### [ThrottlingMiddleware (throttling.py)](file:///c:/Projects/Vesta/bot/tgbot/middlewares/throttling.py)

Prevents spam and abuse.

- Rate limits user requests.
- Ensures the bot stays within Telegram's API limits.

### [ConfigMiddleware (settings.py)](file:///c:/Projects/Vesta/bot/tgbot/middlewares/settings.py)

Dependency injection for handlers.

- Injects the `config` object into the handler's context.
- Allows handlers to access global settings without importing them directly, facilitating testing.

## Execution Order

Middlewares are typically registered in `bot.py` and execute in the order they are added. Outer middlewares run for every update, while inner middlewares might only run if a capable handler is found.
