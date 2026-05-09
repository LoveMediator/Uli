import logging
import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_DEFAULT_KEY = "0123456789abcdef0123456789abcdef"


class Settings(BaseSettings):
    debug: bool = False
    database_url: str = "postgresql+psycopg://user:pass@localhost:5432/app"
    redis_url: str = "redis://localhost:6379/0"
    analysis_session_ttl_seconds: int = 86400
    max_upload_size_mb: int = 5
    llm_provider: str = ""
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_text_model: str = ""
    llm_vision_model: str = ""
    llm_auth_scheme: str = ""
    kimi_api_key: str = ""
    kimi_base_url: str = "https://api.moonshot.cn/v1"
    kimi_text_model: str = "kimi-k2.5"
    kimi_vision_model: str = "moonshot-v1-vision-preview"
    # 逗号分隔的前端源（如 http://localhost:5173）；空字符串表示不启用 CORS 中间件
    cors_origins: str = ""
    db_connect_timeout_seconds: int = 15
    secret_key: str = _INSECURE_DEFAULT_KEY
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def effective_llm_provider(self) -> str:
        return (self.llm_provider or "kimi").strip().lower()

    @property
    def effective_llm_api_key(self) -> str:
        return self.llm_api_key or self.kimi_api_key

    @property
    def effective_llm_base_url(self) -> str:
        return self.llm_base_url or self.kimi_base_url

    @property
    def effective_llm_text_model(self) -> str:
        return self.llm_text_model or self.kimi_text_model

    @property
    def effective_llm_vision_model(self) -> str:
        return self.llm_vision_model or self.kimi_vision_model

    @property
    def effective_llm_auth_scheme(self) -> str:
        if self.llm_auth_scheme:
            return self.llm_auth_scheme.strip().lower()
        if self.effective_llm_provider in {"xiaomi", "mimo"}:
            return "api-key"
        return "bearer"


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
