"""Environment-backed configuration for the conversational agent."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_OPENROUTER_MODEL = "google/gemini-2.5-flash"
DEFAULT_SYSTEM_ONE_ENDPOINT = "https://openrouter.ai/api/alpha/decisions"


class AgentSettings(BaseSettings):
    """Settings loaded from the environment and an optional local ``.env``."""

    model_config = SettingsConfigDict(
        env_file=(".env",),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    openrouter_api_key: SecretStr | None = Field(
        default=None,
        validation_alias="OPENROUTER_API_KEY",
    )
    openrouter_model: str = Field(
        default=DEFAULT_OPENROUTER_MODEL,
        validation_alias="OPENROUTER_MODEL",
        min_length=1,
    )
    system_one_model: str | None = Field(
        default=None,
        validation_alias="SYSTEM_ONE_MODEL",
    )
    system_one_endpoint: str = Field(
        default=DEFAULT_SYSTEM_ONE_ENDPOINT,
        validation_alias="SYSTEM_ONE_ENDPOINT",
        min_length=1,
    )
    system_one_timeout: float = Field(
        default=30.0,
        validation_alias="SYSTEM_ONE_TIMEOUT",
        gt=0,
    )
    tavily_api_key: SecretStr | None = Field(
        default=None,
        validation_alias="TAVILY_API_KEY",
    )
    langsmith_tracing: bool = Field(
        default=False,
        validation_alias="LANGSMITH_TRACING",
    )
    langsmith_endpoint: str | None = Field(
        default=None,
        validation_alias="LANGSMITH_ENDPOINT",
    )
    langsmith_api_key: SecretStr | None = Field(
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
    langfuse_secret_key: SecretStr | None = Field(
        default=None,
        validation_alias="LANGFUSE_SECRET_KEY",
    )
    langfuse_public_key: SecretStr | None = Field(
        default=None,
        validation_alias="LANGFUSE_PUBLIC_KEY",
    )
    langfuse_base_url: str | None = Field(
        default=None,
        validation_alias="LANGFUSE_BASE_URL",
    )

    def require_openrouter_api_key(self) -> str:
        """Return the configured key or raise an actionable configuration error."""

        if self.openrouter_api_key is None:
            raise ValueError("OPENROUTER_API_KEY is required to create the model")
        api_key = self.openrouter_api_key.get_secret_value().strip()
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY must not be empty")
        return api_key

    def require_system_one_model(self) -> str:
        """Return the configured decision model or raise an actionable error."""

        if self.system_one_model is None or not self.system_one_model.strip():
            raise ValueError("SYSTEM_ONE_MODEL is required to create SystemOne")
        return self.system_one_model.strip()


settings = AgentSettings()

__all__ = [
    "DEFAULT_OPENROUTER_MODEL",
    "DEFAULT_SYSTEM_ONE_ENDPOINT",
    "AgentSettings",
    "settings",
]
