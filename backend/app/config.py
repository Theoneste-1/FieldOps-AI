from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "FieldOps AI"
    app_env: str = "development"
    app_debug: bool = True
    secret_key: str = "change-me-to-a-long-random-string"
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:8080,http://localhost:3000,http://127.0.0.1:8080"

    database_url: str = "sqlite+aiosqlite:///./.data/fieldops.db"
    auto_create_tables: bool = True
    seed_demo_data: bool = True

    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    refresh_token_expire_days: int = 14

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_timeout_seconds: int = 25
    gemini_max_retries: int = 2

    upload_dir: str = "./uploads"
    max_upload_mb: int = 15
    auto_create_work_order_on_critical: bool = True

    prometheus_enabled: bool = True
    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.is_sqlite:
        db_path = settings.database_url.split("///")[-1]
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return settings
