"""Request routing workflow nodes."""

from __future__ import annotations

from typing import Any, Literal

from langchain_core.runnables import Runnable
from langgraph.runtime import Runtime

from archwise_agent.core import ArchHypoState, RequestRouting, RunContext
from archwise_agent.graph import GraphNode, raise_if_cancelled

RouteTarget = Literal[
    "direct_response_generation",
    "hypothesis_formulation",
    "architectural_uncertainty_discovery",
]


def create_request_routing_node(
    request_router_agent: Runnable[Any, Any],
) -> GraphNode[ArchHypoState, RunContext]:
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
        # These fields belong to the current turn. Resetting them prevents a
        # previous ArchWise result from leaking into a later direct response.
        return {
            "routing": routing,
            "discovery": None,
            "response": None,
            "hypothesis": None,
            "classification": None,
            "technical_plan": None,
            "result": None,
        }

    return request_router


def route_request(state: ArchHypoState) -> RouteTarget:
    """Select the next graph node from the routing decision."""

    routing = state.get("routing")
    if routing is None:
        raise ValueError("request routing is required")
    if routing.route == "direct_response":
        return "direct_response_generation"
    if routing.route == "uncertainty_discovery":
        return "architectural_uncertainty_discovery"
    return "hypothesis_formulation"


__all__ = ["RouteTarget", "create_request_routing_node", "route_request"]
