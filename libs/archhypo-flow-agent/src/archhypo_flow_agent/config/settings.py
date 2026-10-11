"""Environment-backed configuration for the conversational agent."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_OPENROUTER_MODEL = "google/gemini-2.5-flash"


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

    def require_openrouter_api_key(self) -> str:
        """Return the configured key or raise an actionable configuration error."""

        if self.openrouter_api_key is None:
            raise ValueError("OPENROUTER_API_KEY is required to create the model")
        api_key = self.openrouter_api_key.get_secret_value().strip()
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY must not be empty")
        return api_key


settings = AgentSettings()

__all__ = ["DEFAULT_OPENROUTER_MODEL", "AgentSettings", "settings"]
