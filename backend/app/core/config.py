from functools import lru_cache

from pydantic import SecretStr, field_validator, model_validator
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
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/vesta"

    # General
    DEBUG: bool = True

    # Superuser
    SUPERUSER_EMAIL: str = "admin@admin.com"
    SUPERUSER_PASSWORD: str = "admin"

    # Security - JWT Authentication
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Security - API Key for service-to-service communication
    BACKEND_API_KEY: str = "your-backend-api-key-here"
    CRON_SECRET_KEY: str = "dev-cron-secret-key"

    # GCP
    GCP_LOG_NAME: str = "vesta-backend"
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    GOOGLE_API_KEY: str = ""
    GOOGLE_MODEL_NAME: str = ""
    SYSTEM_INSTRUCTION: str = "You are Vesta, a helpful smart home assistant."
    TELEGRAM_HTML_GUIDELINES: str = (
        "--- TELEGRAM HTML FORMATTING RULES ---\n"
        "You must format all your final user-facing text using HTML tags compatible with Telegram parse mode.\n"
        "Allowed HTML tags:\n"
        "- <b>bold</b> (use <b> instead of Markdown **)\n"
        "- <i>italic</i> (use <i> instead of Markdown *)\n"
        "- <code>code</code> (use <code> instead of backticks `)\n"
        '- <a href="URL">link text</a> (use <a> instead of [text](url))\n'
        "CRITICAL: Never output Markdown formatting (such as **, *, `). Always translate them to equivalent HTML tags. "
        "Malformed or unclosed tags will break the message delivery, so ensure all HTML tags are closed correctly."
    )
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: SecretStr = SecretStr("")
    GOOGLE_REDIRECT_URI: str = ""
    GMAIL_BODY_TRUNCATE_LEN: int = 1500

    # RAG / Knowledge Base
    GOOGLE_DRIVE_FOLDER_ID: str = ""
    CHROMA_DB_PATH: str = "./chroma_db"
    RAG_SIMILARITY_TOP_K: int = 5
    RAG_SIMILARITY_CUTOFF: float = 0.45
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 200

    @field_validator("RAG_CHUNK_SIZE")
    @classmethod
    def validate_chunk_size(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("RAG_CHUNK_SIZE must be greater than 0")
        return v

    @model_validator(mode="after")
    def validate_overlap(self) -> "Settings":
        if self.RAG_CHUNK_OVERLAP < 0:
            raise ValueError("RAG_CHUNK_OVERLAP must be non-negative")
        if self.RAG_CHUNK_OVERLAP >= self.RAG_CHUNK_SIZE:
            raise ValueError(
                "RAG_CHUNK_OVERLAP must be strictly less than RAG_CHUNK_SIZE"
            )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="allow",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
