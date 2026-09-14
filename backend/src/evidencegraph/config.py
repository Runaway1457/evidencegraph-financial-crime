from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="EG_",
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    environment: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    auth_mode: Literal["development", "oidc"] = "development"
    max_upload_bytes: int = Field(default=25 * 1024 * 1024, gt=0)


@lru_cache
def get_settings() -> Settings:
    return Settings()
