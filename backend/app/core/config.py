from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    debug: bool = False
    database_url: str = "postgresql+psycopg://user:pass@localhost:5432/app"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
