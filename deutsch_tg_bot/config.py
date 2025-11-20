from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    TELEGRAM_BOT_TOKEN: str = ""
    ANTHROPIC_API_KEY: str = ""
    # https://docs.anthropic.com/en/docs/about-claude/models/overview#model-names
    ANTHROPIC_MODEL: str = "claude-sonnet-4-5"


settings = Settings()
