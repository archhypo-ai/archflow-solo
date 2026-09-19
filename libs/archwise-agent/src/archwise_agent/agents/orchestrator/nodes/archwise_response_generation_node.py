"""ArchWise conversational response node."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import Runnable
from langgraph.runtime import Runtime

from archwise_agent.core import ArchHypo, ArchHypoState, RunContext, UserResponse
from archwise_agent.graph import GraphNode, raise_if_cancelled

from .direct_response_generation_node import response_history


def create_archwise_response_generation_node(
    response_agent: Runnable[Any, Any],
) -> GraphNode[ArchHypoState, RunContext]:
    """Create the LLM node that explains an ArchWise result conversationally."""

    def respond(
        state: ArchHypoState,
        runtime: Runtime[RunContext] | None = None,
    ) -> dict[str, object]:
        raise_if_cancelled(runtime)
        raw_result = state.get("result")
        if raw_result is None:
            raise ValueError("ArchWise result is required before responding")
        result = (
            raw_result
            if isinstance(raw_result, ArchHypo)
            else ArchHypo.model_validate(raw_result)
        )
        messages = response_history(state["messages"])
        messages.append(
            HumanMessage(
                content=(
                    "Explain this ArchHypo result in the same language as the "
                    "latest user request. Treat it as the source of truth:\n"
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
            "messages": [
                AIMessage(
                    name="archwise_response_agent",
                    content=response.message,
                )
            ],
        }

    return respond


__all__ = ["create_archwise_response_generation_node"]
