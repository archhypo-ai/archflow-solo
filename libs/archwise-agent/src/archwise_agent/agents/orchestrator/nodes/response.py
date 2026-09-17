"""Final response workflow node."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import Runnable
from langgraph.runtime import Runtime

from archwise_agent.core import ArchHypoState, RunContext, UserResponse
from archwise_agent.graph import GraphNode, raise_if_cancelled


def create_response_node(
    response_agent: Runnable[Any, Any],
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
            response_agent.invoke({"messages": messages})
        )
        raise_if_cancelled(runtime)
        return {
            "response": response.message,
            "messages": [AIMessage(name="response_agent", content=response.message)],
        }

    return respond


def response_history(messages: list[Any]) -> list[Any]:
    """Keep internal workflow messages out of the final response prompt."""

    return [
        message
        for message in messages
        if (
            isinstance(message, HumanMessage)
            and not is_internal_history_message(message)
        )
        or (
            isinstance(message, AIMessage)
            and getattr(message, "name", None) == "response_agent"
        )
    ]


def is_internal_history_message(message: Any) -> bool:
    """Exclude prompts from older workflow implementations."""

    if getattr(message, "name", None) in {
        "hypothesis_agent",
        "classifier_agent",
        "technical_plan_agent",
    }:
        return True
    content = getattr(message, "content", "")
    return isinstance(content, str) and "{input}" in content and "{/input}" in content


__all__ = [
    "create_response_node",
    "is_internal_history_message",
    "response_history",
]
