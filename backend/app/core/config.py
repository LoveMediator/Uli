import logging
import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_DEFAULT_KEY = "0123456789abcdef0123456789abcdef"


class Settings(BaseSettings):
    debug: bool = False
    database_url: str = "postgresql+psycopg://user:pass@localhost:5432/app"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = _INSECURE_DEFAULT_KEY
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()

if settings.secret_key == _INSECURE_DEFAULT_KEY:
    if settings.debug:
        logging.getLogger(__name__).warning(
            "SECRET_KEY 使用了不安全的默认值，仅限本地开发使用。"
            "生产环境必须通过环境变量 SECRET_KEY 设置强随机密钥。"
        )
    else:
        settings.secret_key = secrets.token_hex(32)
        logging.getLogger(__name__).warning(
            "SECRET_KEY 未配置，已自动生成随机密钥。"
            "注意：每次重启后令牌将失效。生产环境请通过环境变量配置固定密钥。"
        )
