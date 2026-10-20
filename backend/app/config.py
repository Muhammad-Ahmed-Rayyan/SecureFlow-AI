# config.py — reads all environment variables via pydantic-settings
# Every secret lives in .env (local) or Cloud Run env vars (prod); never hardcoded here.

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_env: str = "local"
    api_key: str = "change-me"

    # Store
    store_backend: Literal["memory", "firestore"] = "memory"
    gcp_project_id: str = ""
    gcp_region: str = "asia-south1"

    # OpenAI
    openai_api_key: str = ""
    openai_model_fast: str = "gpt-4o-mini"
    openai_model_code: str = "gpt-4o"

    # GitHub
    github_token: str = ""
    github_owner: str = ""
    target_repo: str = "secureflow-demo-target"
    target_base_branch: str = "main"

    # Agent limits
    supported_languages: str = "py"
    max_concurrent_runs: int = 3
    max_total_runs: int = 100
    max_fix_attempts: int = 2
    sandbox_timeout_seconds: int = 60
    max_patch_changed_lines: int = 80

    # Frontend
    frontend_origin: str = "http://localhost:3000"

    @property
    def supported_language_list(self) -> list[str]:
        return [lang.strip() for lang in self.supported_languages.split(",") if lang.strip()]


settings = Settings()
