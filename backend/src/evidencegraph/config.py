from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
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
    auth_mode: Literal["development", "signed_jwt"] = "development"
    jwt_secret: SecretStr | None = None
    jwt_issuer: str = "evidencegraph"
    jwt_audience: str = "evidencegraph-api"
    opa_url: str | None = None
    database_url: str = "sqlite+pysqlite:///./evidencegraph.db"
    object_store_path: str = "./var/evidence-objects"
    max_upload_bytes: int = Field(default=25 * 1024 * 1024, gt=0)
    outbox_lease_seconds: int = Field(default=30, ge=5, le=300)
    outbox_max_attempts: int = Field(default=10, ge=1, le=100)
    outbox_poll_seconds: float = Field(default=1.0, ge=0.1, le=60)

    @model_validator(mode="after")
    def validate_security_profile(self) -> "Settings":
        if self.auth_mode == "signed_jwt" and self.jwt_secret is None:
            raise ValueError("EG_JWT_SECRET is required when signed_jwt authentication is enabled")
        if self.environment == "production" and self.auth_mode == "development":
            raise ValueError("development authentication is forbidden in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
