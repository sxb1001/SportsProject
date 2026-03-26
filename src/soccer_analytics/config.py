from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./data/soccer_analytics.db"
    raw_database_url: str = "sqlite:///./data/soccer_analytics.db"
    aws_region: str = "us-east-1"
    s3_bucket: str = "soccer-analytics-raw"
    sports_provider: str = "api_football"
    sports_api_base_url: str = "https://v3.football.api-sports.io"
    sports_api_key: str = ""
    sports_api_host: str = "v3.football.api-sports.io"
    api_football_requests_per_minute: int = 9
    default_league_code: str = "TOP5"
    default_season: int = 2024

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
