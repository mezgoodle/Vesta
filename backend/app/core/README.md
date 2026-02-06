# Core Infrastructure

The `core` directory contains the foundational components of the application that are used throughout the system.

## Components

### [Configuration (config.py)](file:///c:/Projects/Vesta/backend/app/core/config.py)

Manages application settings using `pydantic-settings`.

- Loads environment variables from `.env`.
- Validates configuration values (e.g., ensuring API keys are present).
- Provides a singleton `settings` object used across the app.

### [Logging (logger.py)](file:///c:/Projects/Vesta/backend/app/core/logger.py)

Configures the application's logging behavior.

- Sets up log formats and handlers.
- Supports different logging levels (DEBUG, INFO, ERROR).
- Can be configured to output to console or files.

### [Scheduler (scheduler.py)](file:///c:/Projects/Vesta/backend/app/core/scheduler.py)

Manages background tasks using `APScheduler`.

- Handling periodic tasks like refreshing tokens or polling for updates.
- **Key Functions**:
  - `start_scheduler()`: Initializes the scheduler on app startup.
  - `shutdown_scheduler()`: Gracefully stops tasks on app shutdown.

### [Security (security.py)](file:///c:/Projects/Vesta/backend/app/core/security.py)

Handles cryptographic operations and token management.

- **Password Hashing**: Uses `passlib` with bcrypt for secure password storage.
- **JWT**: Generates and verifies JSON Web Tokens for authentication.
- **Utilities**: `verify_password`, `get_password_hash`, `create_access_token`.
