from pydantic_settings import BaseSettings, SettingsConfigDict

from deutsch_tg_bot.deutsh_enums import DeutschLevel


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    USERNAME_WHITELIST: list[str] = []

    TELEGRAM_BOT_TOKEN: str = ""
    GOOGLE_API_KEY: str = ""

    PREVIOUS_SENTENCES_NUMBER: int = 5
    SHOW_TOCKENS_USAGE: bool = False
    SHOW_FULL_AI_RESPONSE: bool = True
    DEUTSCH_LEVELS: list[DeutschLevel] = [
        DeutschLevel.A1,
        DeutschLevel.A2,
        DeutschLevel.B1,
        DeutschLevel.B2,
    ]

    DEV_SKIP_SENTENCE_CONSTRAINT: bool = False


settings = Settings()
