"""Hypothesis assessment workflow node."""

from __future__ import annotations

from typing import Any

from langchain_core.runnables import Runnable
from langgraph.runtime import Runtime

from archwise_agent.agents.hypothesis_assessor.hypothesis_assessor_agent import (
    make_hypothesis_assessment_input,
)
from archwise_agent.core import (
    ArchHypoState,
    HypothesisClassification,
    RunContext,
)
from archwise_agent.graph import GraphNode, agent_message, raise_if_cancelled


def create_hypothesis_assessment_node(
    hypothesis_assessor_agent: Runnable[Any, Any],
) -> GraphNode[ArchHypoState, RunContext]:
    """Create the node that assesses NFR, impact, and uncertainty."""

    def assess_hypothesis(
        state: ArchHypoState,
        runtime: Runtime[RunContext] | None = None,
    ) -> dict[str, object]:
        raise_if_cancelled(runtime)
        hypothesis = state.get("hypothesis")
        if hypothesis is None:
            raise ValueError("hypothesis is required before assessment")

        classification = HypothesisClassification.model_validate(
            hypothesis_assessor_agent.invoke(
                make_hypothesis_assessment_input(
                    state["uncertainty"],
                    hypothesis.model_dump_json(indent=2),
                )
            )
        )
        raise_if_cancelled(runtime)
        return {
            "classification": classification,
            "messages": [agent_message("hypothesis_assessor_agent", classification)],
        }

    return assess_hypothesis


__all__ = ["create_hypothesis_assessment_node"]
