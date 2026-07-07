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

### [Security (security.py)](file:///c:/Projects/Vesta/backend/app/core/security.py)

Handles cryptographic operations and token management.

- **Password Hashing**: Uses `passlib` with bcrypt for secure password storage.
- **JWT**: Generates and verifies JSON Web Tokens for authentication.
- **Utilities**: `verify_password`, `get_password_hash`, `create_access_token`.
