from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Vesta Smart Assistant"
    API_V1_STR: str = "/api/v1"

    # External APIs
    OPENAI_API_KEY: str
    HOME_ASSISTANT_URL: str
    HOME_ASSISTANT_TOKEN: str
    TELEGRAM_BOT_TOKEN: str

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./vesta.db"
    DEBUG: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
