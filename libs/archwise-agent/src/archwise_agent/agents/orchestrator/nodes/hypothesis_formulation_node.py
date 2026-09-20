"""Hypothesis workflow node."""

from __future__ import annotations

from typing import Any

from langchain_core.runnables import Runnable
from langgraph.runtime import Runtime

from archwise_agent.agents.hypothesis_formulator.hypothesis_formulator_agent import (
    make_hypothesis_input,
)
from archwise_agent.core import ArchHypoState, Hypothesis, RunContext
from archwise_agent.graph import GraphNode, agent_message, raise_if_cancelled


def create_hypothesis_formulation_node(
    hypothesis_formulator_agent: Runnable[Any, Any],
) -> GraphNode[ArchHypoState, RunContext]:
    """Create the node that formulates one testable hypothesis."""

    def formulate_hypothesis(
        state: ArchHypoState,
        runtime: Runtime[RunContext] | None = None,
    ) -> dict[str, object]:
        raise_if_cancelled(runtime)
        hypothesis = Hypothesis.model_validate(
            hypothesis_formulator_agent.invoke(
                make_hypothesis_input(
                    state["uncertainty"],
                    state.get("discovery"),
                )
            )
        )
        raise_if_cancelled(runtime)
        return {
            "uncertainty": hypothesis.uncertainty,
            "hypothesis": hypothesis,
            "messages": [agent_message("hypothesis_formulator_agent", hypothesis)],
        }

    return formulate_hypothesis


__all__ = ["create_hypothesis_formulation_node"]
