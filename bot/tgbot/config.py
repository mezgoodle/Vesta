from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: SecretStr
    admins: list[int] = [353057906]
    backend_base_url: str = "http://localhost:8000"

    # Logging
    DEBUG: bool = False
    GCP_LOG_NAME: str = "vesta-bot"
    GOOGLE_APPLICATION_CREDENTIALS: str = "logger_sa.json"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


config = Settings()
