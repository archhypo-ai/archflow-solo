"""Deterministic initial routing for the current validation workflow."""

from langgraph.runtime import Runtime

from archhypo_flow_agent.core import AgentRunContext, AgentState, RequestRouting


def request_routing_node(
    _state: AgentState,
    _runtime: Runtime[AgentRunContext] | None = None,
) -> dict[str, object]:
    """Always start the ArchHypo path at architectural uncertainty discovery."""

    return {
        "routing": RequestRouting(),
        "discovery": None,
        "uncertainty": None,
        "hypothesis": None,
        "hypothesis_review": None,
        "hypothesis_feedback": None,
        "assessment": None,
        "technical_plan": None,
        "technical_plan_review": None,
        "technical_plan_feedback": None,
        "result": None,
    }


__all__ = ["request_routing_node"]
