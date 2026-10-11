"""OpenRouter chat model factory."""

from langchain_openrouter import ChatOpenRouter

from archhypo_flow_agent.config import AgentSettings, settings


def create_openrouter_model(
    configuration: AgentSettings | None = None,
) -> ChatOpenRouter:
    """Create the native LangChain OpenRouter integration."""

    resolved = configuration or settings
    model = resolved.openrouter_model.removeprefix("openrouter:")
    return ChatOpenRouter(
        api_key=resolved.require_openrouter_api_key(),
        model=model,
        temperature=0,
    )


__all__ = ["create_openrouter_model"]
