"""Jev-backed request routing with an LLM fallback."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_core.runnables import Runnable, RunnableLambda

from archwise_agent.config import AgentSettings
from archwise_agent.core import RequestRouting
from archwise_agent.providers import (
    JevDecisionClient,
    JevError,
    JevResponseError,
)

logger = logging.getLogger(__name__)

_ROUTE_QUESTION = {
    "type": "choice",
    "instructions": "Which workflow should handle this request?",
    "criteria": {
        "direct_response": (
            "A general question, follow-up, explanation, or casual conversation "
            "that does not require architectural analysis."
        ),
        "archwise_workflow": (
            "An architectural uncertainty requiring a hypothesis, classification, "
            "or technical plan."
        ),
    },
}
_VALID_ROUTES = {"direct_response", "archwise_workflow"}


def build_jev_request_router(
    *,
    configuration: AgentSettings,
    fallback_agent: Runnable[Any, Any],
    client: JevDecisionClient | None = None,
) -> Runnable[Any, RequestRouting]:
    """Build a Jev router that falls back to the existing LLM router."""

    jev_client = client or JevDecisionClient(
        api_key=configuration.openrouter_api_key,
        model=configuration.jev_model,
        endpoint=configuration.jev_endpoint,
        timeout=configuration.jev_timeout,
    )

    def route(payload: dict[str, Any]) -> RequestRouting:
        try:
            decision = jev_client.decide(
                state=_latest_user_message(payload.get("messages", [])),
                questions={"route": _ROUTE_QUESTION},
            )
            answer = decision.answers.get("route")
            if answer is None or answer.choice not in _VALID_ROUTES:
                raise JevResponseError("Jev returned an invalid route")
            return RequestRouting(
                route=answer.choice,
                confidence=answer.confidence,
                probabilities=answer.probabilities,
            )
        except JevError as error:
            logger.warning("Jev routing failed; using the LLM fallback: %s", error)
            return RequestRouting.model_validate(fallback_agent.invoke(payload))

    return RunnableLambda(route).with_config(
        {"run_name": "jev_request_router", "tags": ["jev", "routing"]}
    )


def _latest_user_message(messages: list[Any]) -> str:
    """Use the current user message as the compact Jev decision state."""

    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            content = message.content
            if isinstance(content, str) and content.strip():
                return content
    raise JevResponseError("No user message is available for Jev routing")


__all__ = ["build_jev_request_router"]
