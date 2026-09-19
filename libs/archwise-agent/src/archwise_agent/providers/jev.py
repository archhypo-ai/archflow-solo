"""Generic Jev decision client."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError


class JevError(RuntimeError):
    """Base error for Jev decision requests."""


class JevRequestError(JevError):
    """Jev could not be reached or rejected the request."""


class JevResponseError(JevError):
    """Jev returned a response that could not be used."""


class JevAnswer(BaseModel):
    """Generic typed answer returned by a Jev decision."""

    type: str
    choice: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    probabilities: dict[str, float] | None = None
    noul: float | None = Field(default=None, ge=0.0, le=1.0)
    score: float | None = None


class JevUsage(BaseModel):
    """Usage reported by the decision provider."""

    input_tokens: int | None = None
    output_tokens: int | None = None
    cost: float | None = None


class JevDecisionResponse(BaseModel):
    """Generic response containing named Jev answers."""

    model: str
    answers: dict[str, JevAnswer]
    usage: JevUsage = Field(default_factory=JevUsage)
    id: str | None = None
    provider: str | None = None


class JevDecisionClient:
    """Stateless HTTP client for a Jev-compatible Decisions endpoint."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        endpoint: str,
        timeout: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._endpoint = endpoint
        self._timeout = timeout

    def decide(
        self,
        *,
        state: str | dict[str, Any] | list[Any],
        questions: Mapping[str, Mapping[str, Any]],
        session_id: str | None = None,
    ) -> JevDecisionResponse:
        """Submit structured questions about ``state`` to Jev."""

        if not self._api_key.strip():
            raise JevRequestError("Jev API key is not configured")

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
                    "User-Agent": "archwise-agent",
                },
                json=payload,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            status = getattr(error.response, "status_code", None)
            suffix = f" (status={status})" if status is not None else ""
            raise JevRequestError(f"Jev request failed{suffix}") from error

        try:
            body = response.json()
            return JevDecisionResponse.model_validate(body)
        except (ValueError, ValidationError) as error:
            raise JevResponseError("Jev returned an invalid response") from error


__all__ = [
    "JevAnswer",
    "JevDecisionClient",
    "JevDecisionResponse",
    "JevError",
    "JevRequestError",
    "JevResponseError",
    "JevUsage",
]
