"""OpenRouter model provider."""

from __future__ import annotations

from langchain_openrouter import ChatOpenRouter

from archwise_agent.config import AgentSettings, settings


def create_openrouter_model(
    configuration: AgentSettings | None = None,
) -> ChatOpenRouter:
    """Create the official LangChain OpenRouter chat integration."""

    resolved = configuration or settings
    kwargs: dict[str, object] = {
        "api_key": resolved.require_openrouter_api_key(),
        "model": _api_model_name(resolved.openrouter_model),
        "temperature": 0,
    }
    if resolved.openrouter_http_referer:
        kwargs["app_url"] = resolved.openrouter_http_referer
    if resolved.openrouter_app_name:
        kwargs["app_title"] = resolved.openrouter_app_name

    return ChatOpenRouter(**kwargs)


def _api_model_name(model_identifier: str) -> str:
    prefix = "openrouter:"
    if model_identifier.startswith(prefix):
        return model_identifier.removeprefix(prefix)
    return model_identifier


__all__ = ["create_openrouter_model"]
