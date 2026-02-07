from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


def _root_env_path() -> Path:
    """Resolve path to monorepo root .env (parent of backend)."""
    return Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """All app and database configuration via pydantic-settings from root .env / environment."""

    model_config = SettingsConfigDict(
        env_file=_root_env_path() if _root_env_path().exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App (externalized)
    APP_NAME: str = "Tutor App (NCERT Tracker)"
    ADMIN_EMAIL: str = "admin@tutorapp.local"

    # Database — DATABASE_URL takes precedence; otherwise built from components (all externalized)
    DATABASE_URL: str | None = None
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_NAME: str = "tutor_app_db"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # Logging — configurable file and level; LOG_FORMAT=json for structured stdout (e.g. Coolify/container)
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/backend.log"  # Relative to backend dir or absolute; set to "" for console only
    LOG_FORMAT: str = "json"  # "json" (one JSON object per line to stdout) or "text"

    @property
    def database_url(self) -> str:
        """Async Postgres URL with quoted user/password (safe for special characters)."""
        if self.DATABASE_URL and self.DATABASE_URL.strip():
            url = self.DATABASE_URL.strip()
            return url if url.startswith("postgresql+asyncpg://") else url.replace("postgresql://", "postgresql+asyncpg://", 1)
        user = quote_plus(self.DB_USER)
        password = quote_plus(self.DB_PASSWORD)
        return (
            f"postgresql+asyncpg://{user}:{password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
