from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Vesta Smart Assistant"
    API_V1_STR: str = "/api/v1"

    # External APIs - Optional for testing
    OPENAI_API_KEY: str = "test-key"
    HOME_ASSISTANT_URL: str = "http://localhost:8123"
    HOME_ASSISTANT_TOKEN: str = "test-token"
    TELEGRAM_BOT_TOKEN: str = "test-bot-token"
    OPENWEATHER_API_KEY: str = "test-weather-key"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./vesta.db"

    # General
    DEBUG: bool = True

    # Security - JWT Authentication
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Security - API Key for service-to-service communication
    BACKEND_API_KEY: str = "your-backend-api-key-here"

    # GCP
    GCP_LOG_NAME: str = "vesta-backend"
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    GOOGLE_API_KEY: str = ""
    GOOGLE_MODEL_NAME: str = ""
    SYSTEM_INSTRUCTION: str = "You are Vesta, a helpful smart home assistant."

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
