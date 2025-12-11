from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    TELEGRAM_BOT_TOKEN: str = ""
    GOOGLE_API_KEY: str = ""

    PREVIOUS_SENTENCES_NUMBER: int = 5
    SHOW_TOCKENS_USAGE: bool = False
    SHOW_FULL_AI_RESPONSE: bool = False


settings = Settings()
