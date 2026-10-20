"""Human review gate for the assessed technical plan."""

from langgraph.runtime import Runtime
from langgraph.types import interrupt

from archhypo_flow_agent.core import AgentRunContext, AgentState, TechnicalPlanReview

from .support import human_review_enabled


def technical_plan_review_node(
    state: AgentState,
    runtime: Runtime[AgentRunContext] | None = None,
) -> dict[str, object]:
    """Pause before the final response unless review is disabled for this run."""

    assessment = state.get("assessment")
    technical_plan = state.get("technical_plan")
    if assessment is None or technical_plan is None:
        raise ValueError("assessment and technical plan are required before review")

    if not human_review_enabled(runtime):
        return {"technical_plan_review": None, "technical_plan_feedback": None}

    decision = TechnicalPlanReview.model_validate(
        interrupt(
            {
                "kind": "technical_plan_review",
                "assessment": assessment.model_dump(mode="json"),
                "technical_plan": technical_plan.model_dump(mode="json"),
            }
        )
    )
    update: dict[str, object] = {
        "technical_plan_review": decision,
        "technical_plan_feedback": (
            decision.reason if decision.decision == "rejected" else None
        ),
    }
    if decision.decision == "approved":
        review_history = list(state.get("review_history", []))
        review_history.append(
            {
                "kind": "technical_plan_review",
                "review": {
                    "kind": "technical_plan_review",
                    "assessment": assessment.model_dump(mode="json"),
                    "technical_plan": technical_plan.model_dump(mode="json"),
                },
                "decision": decision.model_dump(mode="json"),
                "after_message_count": len(state.get("messages", [])),
            }
        )
        update["review_history"] = review_history
    return update


def route_after_technical_plan_review(
    state: AgentState,
    runtime: Runtime[AgentRunContext] | None = None,
) -> str:
    """Finalize after approval or bypass; otherwise generate a revised plan."""

    if not human_review_enabled(runtime):
        return "response_generation"

    decision = state.get("technical_plan_review")
    if decision is None:
        raise ValueError("a human decision is required after technical plan review")
    return (
        "response_generation"
        if decision.decision == "approved"
        else "technical_plan_generation"
    )


__all__ = ["route_after_technical_plan_review", "technical_plan_review_node"]
