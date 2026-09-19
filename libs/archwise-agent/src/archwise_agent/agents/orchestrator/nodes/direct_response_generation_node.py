"""Direct-response workflow node."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import Runnable
from langgraph.runtime import Runtime

from archwise_agent.core import ArchHypoState, RunContext, UserResponse
from archwise_agent.graph import GraphNode, raise_if_cancelled

_RESPONSE_AGENT_NAMES = {
    "archwise_response_agent",
    "archwise_result_renderer",
    "response_composer_agent",
    "response_agent",
}


def create_direct_response_generation_node(
    response_agent: Runnable[Any, Any],
) -> GraphNode[ArchHypoState, RunContext]:
    """Create the LLM node for requests without an ArchWise result."""

    def respond(
        state: ArchHypoState,
        runtime: Runtime[RunContext] | None = None,
    ) -> dict[str, object]:
        raise_if_cancelled(runtime)
        response = UserResponse.model_validate(
            response_agent.invoke({"messages": response_history(state["messages"])})
        )
        raise_if_cancelled(runtime)
        return {
            "response": response.message,
            "result": None,
            "messages": [
                AIMessage(
                    name="response_composer_agent",
                    content=response.message,
                )
            ],
        }

    return respond


def response_history(messages: list[Any]) -> list[Any]:
    """Keep internal workflow messages out of response prompts."""

    return [
        message
        for message in messages
        if isinstance(message, HumanMessage)
        or (
            isinstance(message, AIMessage)
            and getattr(message, "name", None) in _RESPONSE_AGENT_NAMES
        )
    ]


__all__ = ["create_direct_response_generation_node", "response_history"]
