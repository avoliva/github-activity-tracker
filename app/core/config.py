"""Application configuration and settings management."""

from logging.config import dictConfig
from typing import Optional
from urllib.parse import urlparse

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings and configuration.

    Loads configuration from environment variables or uses defaults.
    Settings can be overridden via .env file or environment variables.

    Attributes:
        api_title: API title for OpenAPI documentation
        api_version: API version string
        debug: Enable debug mode (default: False)
        log_level: Logging level (default: INFO).
            Valid values: DEBUG, INFO, WARNING, ERROR, CRITICAL
        github_api_base_url: Base URL for GitHub API
        cache_ttl_seconds: Cache time-to-live in seconds (default: 600)
        cache_max_size: Maximum number of cache entries (default: 1000)
        request_timeout_seconds: HTTP request timeout in seconds (default: 30)

    """

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    api_title: str = "GitHub Activity Tracker"
    api_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    github_api_base_url: str = "https://api.github.com"
    cache_ttl_seconds: int = 600
    cache_max_size: int = 1000
    request_timeout_seconds: int = 30
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    @field_validator("github_api_base_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL has scheme and netloc (e.g., https://example.com)."""
        try:
            result = urlparse(v)
            if not all([result.scheme, result.netloc]):
                raise ValueError("Invalid URL format")
            return v
        except Exception as e:
            raise ValueError(f"Invalid URL format: {e}")

    @field_validator("cache_ttl_seconds", "cache_max_size", "request_timeout_seconds")
    @classmethod
    def validate_positive_int(cls, v: int) -> int:
        """Ensure value is > 0, raises ValueError otherwise."""
        if v <= 0:
            raise ValueError(f"Value must be positive, got {v}")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of: DEBUG, INFO, WARNING, ERROR, CRITICAL.

        Normalizes to uppercase.
        """
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            valid_levels_str = ", ".join(sorted(valid_levels))
            raise ValueError(f"Invalid log level '{v}'. Must be one of: {valid_levels_str}")
        return v_upper


def get_logging_config(log_level: str = "INFO") -> dict:
    """Get logging configuration dictionary.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Logging configuration dictionary

    """
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["default"],
        },
    }


def setup_logging() -> None:
    """Configure application logging using log level from settings."""
    settings = get_settings()
    logging_config = get_logging_config(settings.log_level)
    dictConfig(logging_config)


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings instance (singleton pattern).

    Returns a singleton instance of Settings, creating it on first call.
    Subsequent calls return the same instance.

    Returns:
        Settings instance with application configuration

    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
