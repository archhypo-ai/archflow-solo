"""Provider-neutral SystemOne contract backed by OpenRouter decisions."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

import httpx
from pydantic import BaseModel, Field, ValidationError

from archhypo_flow_agent.config import AgentSettings, settings


class SystemOneError(RuntimeError):
    """Base error raised by the SystemOne decision boundary."""


class SystemOneRequestError(SystemOneError):
    """SystemOne could not be reached or rejected the request."""


class SystemOneResponseError(SystemOneError):
    """SystemOne returned a response that could not be used."""


class SystemOneAnswer(BaseModel):
    """One typed decision returned for a named question."""

    type: str
    choice: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    probabilities: dict[str, float] | None = None
    noul: float | None = Field(default=None, ge=0.0, le=1.0)
    score: float | None = None


class SystemOneUsage(BaseModel):
    """Usage reported by the decision service."""

    input_tokens: int | None = None
    output_tokens: int | None = None
    cost: float | None = None


class SystemOneResponse(BaseModel):
    """Generic response containing named SystemOne answers."""

    model: str
    answers: dict[str, SystemOneAnswer]
    usage: SystemOneUsage = Field(default_factory=SystemOneUsage)
    id: str | None = None
    provider: str | None = None


class SystemOneClient(Protocol):
    """Decision interface consumed by routing and other orchestration nodes."""

    def decide(
        self,
        *,
        state: str | dict[str, Any] | list[Any],
        questions: Mapping[str, Mapping[str, Any]],
        session_id: str | None = None,
    ) -> SystemOneResponse: ...


class OpenRouterSystemOneClient:
    """OpenRouter adapter for the provider-neutral SystemOne decision contract.

    The configured model identifier is sent as-is, regardless of the model
    vendor. Model selection therefore belongs to configuration, not the graph.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        endpoint: str,
        timeout: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._model = _openrouter_model_name(model)
        self._endpoint = endpoint
        self._timeout = timeout

    def decide(
        self,
        *,
        state: str | dict[str, Any] | list[Any],
        questions: Mapping[str, Mapping[str, Any]],
        session_id: str | None = None,
    ) -> SystemOneResponse:
        """Submit typed decision questions and validate the provider response."""

        if not self._api_key.strip():
            raise SystemOneRequestError("OpenRouter API key is not configured")

        payload: dict[str, Any] = {
            "model": self._model,
            "state": state,
            "questions": dict(questions),
        }
        if session_id is not None:
            payload["session_id"] = session_id

        try:
            response = httpx.post(
                self._endpoint,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "archhypo-flow-agent",
                },
                json=payload,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            response = getattr(error, "response", None)
            status = getattr(response, "status_code", None)
            suffix = f" (status={status})" if status is not None else ""
            raise SystemOneRequestError(
                f"OpenRouter SystemOne request failed{suffix}"
            ) from error

        try:
            return SystemOneResponse.model_validate(response.json())
        except (ValueError, ValidationError) as error:
            raise SystemOneResponseError(
                "OpenRouter SystemOne returned an invalid response"
            ) from error


def create_system_one_client(
    configuration: AgentSettings | None = None,
) -> OpenRouterSystemOneClient:
    """Create SystemOne using shared OpenRouter credentials and model settings."""

    resolved = configuration or settings
    return OpenRouterSystemOneClient(
        api_key=resolved.require_openrouter_api_key(),
        model=resolved.require_system_one_model(),
        endpoint=resolved.system_one_endpoint,
        timeout=resolved.system_one_timeout,
    )


def _openrouter_model_name(model: str) -> str:
    return model.removeprefix("openrouter:").strip()


__all__ = [
    "OpenRouterSystemOneClient",
    "SystemOneAnswer",
    "SystemOneClient",
    "SystemOneError",
    "SystemOneRequestError",
    "SystemOneResponse",
    "SystemOneResponseError",
    "SystemOneUsage",
    "create_system_one_client",
]
