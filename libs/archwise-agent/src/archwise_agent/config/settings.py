"""Typed settings for the ArchWise agent runtime."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_OPENROUTER_MODEL = "openrouter:deepseek/deepseek-v4.1-flash"


class AgentSettings(BaseSettings):
    """Environment-backed configuration for the initial agent.

    Provider-specific fields are explicit for now. A provider-neutral model
    configuration can be introduced later without leaking environment access
    into graph construction or application services.
    """

    model_config = SettingsConfigDict(
        env_file=(".env",),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    openrouter_api_key: str = Field(
        default="",
        validation_alias="OPENROUTER_API_KEY",
    )
    openrouter_model: str = Field(
        default=DEFAULT_OPENROUTER_MODEL,
        validation_alias="OPENROUTER_MODEL",
    )
    openrouter_http_referer: str | None = Field(
        default=None,
        validation_alias="OPENROUTER_HTTP_REFERER",
    )
    openrouter_app_name: str | None = Field(
        default=None,
        validation_alias="OPENROUTER_APP_NAME",
    )
    tavily_api_key: str = Field(
        default="",
        validation_alias="TAVILY_API_KEY",
    )
    archwise_storage_root: Path | None = Field(
        default=None,
        validation_alias="ARCHWISE_STORAGE_ROOT",
    )
    langsmith_tracing: bool = Field(
        default=False,
        validation_alias="LANGSMITH_TRACING",
    )
    langsmith_endpoint: str | None = Field(
        default=None,
        validation_alias="LANGSMITH_ENDPOINT",
    )
    langsmith_api_key: str | None = Field(
        default=None,
        validation_alias="LANGSMITH_API_KEY",
    )
    langsmith_project: str | None = Field(
        default=None,
        validation_alias="LANGSMITH_PROJECT",
    )
    langfuse_enabled: bool = Field(
        default=False,
        validation_alias="LANGFUSE_ENABLED",
    )
    langfuse_secret_key: str | None = Field(
        default=None,
        validation_alias="LANGFUSE_SECRET_KEY",
    )
    langfuse_public_key: str | None = Field(
        default=None,
        validation_alias="LANGFUSE_PUBLIC_KEY",
    )
    langfuse_base_url: str | None = Field(
        default=None,
        validation_alias="LANGFUSE_BASE_URL",
    )

    def require_openrouter_api_key(self) -> str:
        if not self.openrouter_api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is required to create the OpenRouter model"
            )
        return self.openrouter_api_key


settings = AgentSettings()

__all__ = [
    "DEFAULT_OPENROUTER_MODEL",
    "AgentSettings",
    "settings",
]
