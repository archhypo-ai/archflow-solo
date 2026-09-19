"""Final response workflow node."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import Runnable
from langgraph.runtime import Runtime

from archwise_agent.core import ArchHypoState, RunContext, UserResponse
from archwise_agent.graph import GraphNode, raise_if_cancelled

_RESPONSE_AGENT_NAMES = {"response_composer_agent", "response_agent"}


def create_response_composition_node(
    response_composer_agent: Runnable[Any, Any],
) -> GraphNode[ArchHypoState, RunContext]:
    """Create the final node that renders a human-facing response."""

    def respond(
        state: ArchHypoState,
        runtime: Runtime[RunContext] | None = None,
    ) -> dict[str, object]:
        raise_if_cancelled(runtime)
        messages = response_history(state["messages"])
        result = state.get("result")
        if result is not None:
            messages.append(
                HumanMessage(
                    content=(
                        "Compose the final answer from this ArchHypo result:\n"
                        f"{result.model_dump_json(indent=2)}"
                    )
                )
            )

        response = UserResponse.model_validate(
            response_composer_agent.invoke({"messages": messages})
        )
        raise_if_cancelled(runtime)
        return {
            "response": response.message,
            "messages": [
                AIMessage(
                    name="response_composer_agent",
                    content=response.message,
                )
            ],
        }

    return respond


def response_history(messages: list[Any]) -> list[Any]:
    """Keep internal workflow messages out of the final response prompt."""

    return [
        message
        for message in messages
        if isinstance(message, HumanMessage)
        or (
            isinstance(message, AIMessage)
            and getattr(message, "name", None) in _RESPONSE_AGENT_NAMES
        )
    ]


__all__ = ["create_response_composition_node", "response_history"]
