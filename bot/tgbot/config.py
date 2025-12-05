from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: SecretStr
    admins: list[int] = [353057906]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


config = Settings()
