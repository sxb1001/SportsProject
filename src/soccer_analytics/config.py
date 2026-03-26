from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./data/soccer_analytics.db"
    raw_database_url: str = "sqlite:///./data/soccer_analytics.db"
    aws_region: str = "us-east-1"
    s3_bucket: str = "soccer-analytics-raw"
    sports_provider: str = "mock"
    sports_api_base_url: str = "https://example.com"
    sports_api_key: str = ""
    default_league_code: str = "EPL"
    default_season: int = 2024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
