from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: SecretStr
    admins: list[int] = [353057906]
    backend_base_url: str = (
        "https://vesta-backend-1074367258192.europe-central2.run.app"
    )
    backend_api_key: SecretStr

    DEBUG: bool = True

    # Google Cloud
    GCP_PROJECT_ID: str = ""
    GCP_LOG_NAME: str = "vesta-bot"
    GOOGLE_APPLICATION_CREDENTIALS: str = ""

    # Webhook Settings
    WEBHOOK_DOMAIN: str = ""
    WEBHOOK_PATH: str = "/webhook"
    WEBHOOK_SECRET: SecretStr | None = None
    APP_PORT: int = 8080
    APP_HOST: str = "0.0.0.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
    )


config = Settings()
