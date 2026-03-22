"""
app/config.py
Central configuration for the application.
Loads values from environment variables / .env using pydantic-settings.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal, FrozenSet

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Pydantic Config ────────────────────────────────────────────────────
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,   # allows MODEL_NAME → model_name
        extra="ignore",
    )

    # ── App ────────────────────────────────────────────────────────────────
    app_name: str = "Country Intelligence Agent"
    app_version: str = "1.0.0"
    environment: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"

    # ── Anthropic ──────────────────────────────────────────────────────────
    anthropic_api_key: str = ""
    model_name: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = 512

    # ── PostgreSQL ─────────────────────────────────────────────────────────
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "country_agent"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"

    # ── Computed DB URLs ───────────────────────────────────────────────────
    @computed_field
    @property
    def database_url(self) -> str:
        """Async DB URL (for SQLAlchemy async engine)."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field
    @property
    def sync_database_url(self) -> str:
        """Sync DB URL (used by Alembic)."""
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ── REST Countries API ─────────────────────────────────────────────────
    countries_api_base: str = "https://restcountries.com/v3.1"

    countries_api_fields: str = (
        "name,capital,population,currencies,languages,"
        "region,subregion,flags,area,timezones,tld"
    )

    http_timeout_seconds: float = 10.0
    http_max_retries: int = 2

    # ── Agent Config ───────────────────────────────────────────────────────
    supported_fields: FrozenSet[str] = frozenset({
        "capital",
        "population",
        "currencies",
        "languages",
        "region",
        "subregion",
        "flags",
        "area",
        "timezones",
        "tld",
    })

    # ── Query History / Audit ──────────────────────────────────────────────
    max_query_history: int = 1000


# ── Singleton Settings Instance ───────────────────────────────────────────
@lru_cache
def get_settings() -> Settings:
    return Settings()