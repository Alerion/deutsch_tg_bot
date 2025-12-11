from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict


class AIProvider(str, Enum):
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    TELEGRAM_BOT_TOKEN: str = ""
    AI_PROVIDER: AIProvider = AIProvider.GOOGLE
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""

    PREVIOUS_SENTENCES_NUMBER: int = 5
    MOCK_AI: bool = False
    SHOW_TOCKENS_USAGE: bool = False
    SHOW_FULL_AI_RESPONSE: bool = False


settings = Settings()
