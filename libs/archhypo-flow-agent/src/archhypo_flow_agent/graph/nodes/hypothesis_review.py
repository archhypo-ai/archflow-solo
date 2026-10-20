"""Human review gate for the formulated hypothesis."""

from langgraph.runtime import Runtime
from langgraph.types import interrupt

from archhypo_flow_agent.core import AgentRunContext, AgentState, HypothesisReview

from .support import human_review_enabled


def hypothesis_review_node(
    state: AgentState,
    runtime: Runtime[AgentRunContext] | None = None,
) -> dict[str, object]:
    """Pause for a human decision unless review is disabled for this run."""

    hypothesis = state.get("hypothesis")
    if hypothesis is None:
        raise ValueError("a hypothesis is required before human review")

    if not human_review_enabled(runtime):
        return {"hypothesis_review": None, "hypothesis_feedback": None}

    decision = HypothesisReview.model_validate(
        interrupt(
            {
                "kind": "hypothesis_review",
                "hypothesis": hypothesis.model_dump(mode="json"),
            }
        )
    )
    update: dict[str, object] = {
        "hypothesis_review": decision,
        "hypothesis_feedback": (
            decision.reason if decision.decision == "rejected" else None
        ),
    }
    if decision.decision == "approved":
        review_history = list(state.get("review_history", []))
        review_history.append(
            {
                "kind": "hypothesis_review",
                "review": {
                    "kind": "hypothesis_review",
                    "hypothesis": hypothesis.model_dump(mode="json"),
                },
                "decision": decision.model_dump(mode="json"),
                "after_message_count": len(state.get("messages", [])),
            }
        )
        update["review_history"] = review_history
    return update


def route_after_hypothesis_review(
    state: AgentState,
    runtime: Runtime[AgentRunContext] | None = None,
) -> str:
    """Continue after approval or bypass; otherwise reformulate."""

    if not human_review_enabled(runtime):
        return "hypothesis_assessment"

    decision = state.get("hypothesis_review")
    if decision is None:
        raise ValueError("a human decision is required after hypothesis review")
    return (
        "hypothesis_assessment"
        if decision.decision == "approved"
        else "hypothesis_formulation"
    )


__all__ = ["hypothesis_review_node", "route_after_hypothesis_review"]
