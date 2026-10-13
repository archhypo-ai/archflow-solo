"""Human review gate for the formulated hypothesis."""

from langgraph.types import interrupt

from archhypo_flow_agent.core import AgentState, HypothesisReview


def hypothesis_review_node(state: AgentState) -> dict[str, object]:
    """Pause until the user approves the hypothesis or rejects it with a reason."""

    hypothesis = state.get("hypothesis")
    if hypothesis is None:
        raise ValueError("a hypothesis is required before human review")

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


def route_after_hypothesis_review(state: AgentState) -> str:
    """Continue to assessment only after approval; otherwise reformulate."""

    decision = state.get("hypothesis_review")
    if decision is None:
        raise ValueError("a human decision is required after hypothesis review")
    return (
        "hypothesis_assessment"
        if decision.decision == "approved"
        else "hypothesis_formulation"
    )


__all__ = ["hypothesis_review_node", "route_after_hypothesis_review"]
