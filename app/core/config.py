from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    groq_api_key: str = ""
    default_provider: str = "claude"
    claude_model: str = "claude-sonnet-5"
    groq_model: str = "llama-3.3-70b-versatile"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_pr_reviewer"
    github_app_id: str = ""
    github_private_key: str = ""
    github_private_key_path: str = ""
    github_webhook_secret: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
