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

    # GCP
    GCP_LOG_NAME: str = "vesta-backend"
    GOOGLE_APPLICATION_CREDENTIALS: str = "logger_sa.json"

    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
