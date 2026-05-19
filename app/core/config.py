"""
Application configuration management.

This module provides strongly typed application settings using
pydantic-settings. All environment-driven configurations for the
Tradequity backend should be defined here.

Design principles:
    - Fail fast on invalid startup configuration.
    - Strong typing for all settings.
    - Centralized configuration access.
    - Environment-specific overrides via .env

Usage:
    from app.core.config import settings

    database_url = settings.database_url
"""

from functools import lru_cache

from pydantic          import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Strongly typed application settings.

    This class loads configuration from environment variables and the
    configured .env file. Validation occurs at application startup.

    Attributes:
        env:
            Application runtime environment.

        debug:
            Enables debug mode behaviors.

        database_url:
            Async PostgreSQL connection string for SQLAlchemy

        supabase_url:
            Supabase project URL.

        supabase_jwks_url:
            JWKS endpoint used for JWT signature validation.

        supabase_issuer:
            Expected JWT issuer.

        supabase_audience:
            Expected JWT audience.

        supabase_service_role_key:
            Service role key for privileged backend operations.

        market_refresh_interval_seconds:
            Interval for refreshing cached market price.

        stale_market_price_threshold_seconds:
            Threshold after which cached prices are considered stale.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    env  : str = Field(default="development")
    debug: str = Field(default=False)

    database_url: str = Field(...)

    supabase_url             : str = Field(...)
    supabase_jwks_url        : str = Field(...)
    supabase_issuer          : str = Field(...)
    supabase_audience        : str = Field(default="authenticated")
    supabase_service_role_key: str = Field(...)

    market_refresh_interval_seconds     : int = Field(default=300)
    stale_market_price_threshold_seconds: int = Field(default=900)


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached application settings instance.

    Settings are loaded once per process and cached for subsequent access.
    This avoids repeated environment parsing and ensures consistent config
    usage throughout the application lifecycle.

    Returns:
        Settings:
            Validate application configuration instance.
    """
    return Settings()

settings = get_settings()

