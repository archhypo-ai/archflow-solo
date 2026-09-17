"""Hypothesis classification workflow node."""

from __future__ import annotations

from typing import Any

from langchain_core.runnables import Runnable
from langgraph.runtime import Runtime

from archwise_agent.agents.classifier.agent import classifier_input
from archwise_agent.core import (
    ArchHypoState,
    HypothesisClassification,
    RunContext,
)

from .common import Node, agent_message, raise_if_cancelled


def create_classify_hypothesis_node(
    classifier_agent: Runnable[Any, Any],
) -> Node:
    """Create the node that classifies NFR, impact, and uncertainty."""

    def classify_hypothesis(
        state: ArchHypoState,
        runtime: Runtime[RunContext] | None = None,
    ) -> dict[str, object]:
        raise_if_cancelled(runtime)
        hypothesis = state.get("hypothesis")
        if hypothesis is None:
            raise ValueError("hypothesis is required before classification")

        classification = HypothesisClassification.model_validate(
            classifier_agent.invoke(
                classifier_input(
                    state["uncertainty"],
                    hypothesis.model_dump_json(indent=2),
                )
            )
        )
        raise_if_cancelled(runtime)
        return {
            "classification": classification,
            "messages": [agent_message("classifier_agent", classification)],
        }

    return classify_hypothesis


__all__ = ["create_classify_hypothesis_node"]
