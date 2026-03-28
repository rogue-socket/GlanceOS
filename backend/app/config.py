from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "WARNING"
    weather_city: str = "Hyderabad,IN"
    github_username: str = "octocat"
    weather_api_key: str = ""
    github_token: str = ""
    todoist_api_token: str = ""
    google_calendar_id: str = ""
    google_calendar_api_key: str = ""
    google_calendar_ics_url: str = ""
    news_use_llm: bool = True
    news_llm_provider: str = "gemini"
    news_llm_api_key: str = ""
    news_llm_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    news_llm_model: str = "gemini-2.0-flash-lite"
    news_llm_timeout_seconds: float = 12.0
    database_url: str = "sqlite+aiosqlite:///./glanceos.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
