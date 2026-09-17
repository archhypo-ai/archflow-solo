"""Request routing workflow nodes."""

from __future__ import annotations

from typing import Any

from langchain_core.runnables import Runnable
from langgraph.runtime import Runtime

from archwise_agent.core import ArchHypoState, RequestRouting, RunContext

from .common import Node, raise_if_cancelled


def create_request_router_node(
    request_router_agent: Runnable[Any, Any],
) -> Node:
    """Create the node that chooses direct response or ArchWise workflow."""

    def request_router(
        state: ArchHypoState,
        runtime: Runtime[RunContext] | None = None,
    ) -> dict[str, object]:
        raise_if_cancelled(runtime)
        routing = RequestRouting.model_validate(
            request_router_agent.invoke({"messages": state["messages"]})
        )
        raise_if_cancelled(runtime)
        return {"routing": routing}

    return request_router


def route_request(state: ArchHypoState) -> str:
    """Select the next graph node from the routing decision."""

    routing = state.get("routing")
    if routing is None:
        raise ValueError("request routing is required")
    if routing.route == "direct_response":
        return "respond_directly"
    return "formulate_hypothesis"


__all__ = ["create_request_router_node", "route_request"]
