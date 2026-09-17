"""Nodes for the linear ArchHypo workflow."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import Runnable
from langgraph.runtime import Runtime

from archwise_agent.agents.classifier.agent import classifier_input
from archwise_agent.agents.hypothesis.agent import hypothesis_input
from archwise_agent.core import (
    AgentCancelledError,
    ArchHypo,
    ArchHypoState,
    Hypothesis,
    HypothesisClassification,
    RunContext,
    TechnicalPlan,
)

Node = Callable[[ArchHypoState, Runtime[RunContext]], dict[str, object]]


def create_formulate_hypothesis_node(
    hypothesis_agent: Runnable[Any, Any],
) -> Node:
    """Create the node that formulates one hypothesis from one uncertainty."""

    def formulate_hypothesis(
        state: ArchHypoState,
        runtime: Runtime[RunContext] | None = None,
    ) -> dict[str, object]:
        """Formulate exactly one testable architectural hypothesis."""

        _raise_if_cancelled(runtime)
        hypothesis = Hypothesis.model_validate(
            hypothesis_agent.invoke(hypothesis_input(state["uncertainty"]))
        )
        _raise_if_cancelled(runtime)
        return {
            "uncertainty": hypothesis.uncertainty,
            "hypothesis": hypothesis,
            "messages": [_agent_message("hypothesis_agent", hypothesis)],
        }

    return formulate_hypothesis


def create_classify_hypothesis_node(
    classifier_agent: Runnable[Any, Any],
) -> Node:
    """Create the node that classifies NFR, impact, and uncertainty."""

    def classify_hypothesis(
        state: ArchHypoState,
        runtime: Runtime[RunContext] | None = None,
    ) -> dict[str, object]:
        """Classify the hypothesis using independent justifications."""

        _raise_if_cancelled(runtime)
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
        _raise_if_cancelled(runtime)
        return {
            "classification": classification,
            "messages": [_agent_message("classifier_agent", classification)],
        }

    return classify_hypothesis


def create_technical_plan_node(
    technical_plan_agent: Runnable[Any, Any],
) -> Node:
    """Create the node that generates the final technical plan."""

    def create_technical_plan(
        state: ArchHypoState,
        runtime: Runtime[RunContext] | None = None,
    ) -> dict[str, object]:
        """Create three to five mitigation actions from the catalog."""

        _raise_if_cancelled(runtime)
        hypothesis = state.get("hypothesis")
        classification = state.get("classification")
        if hypothesis is None or classification is None:
            raise ValueError(
                "hypothesis and classification are required before planning"
            )

        prompt = (
            "Architectural uncertainty:\n"
            f"{state['uncertainty']}\n\n"
            "Hypothesis:\n"
            f"{hypothesis.model_dump_json(indent=2)}\n\n"
            "Classification:\n"
            f"{classification.model_dump_json(indent=2)}"
        )
        result = technical_plan_agent.invoke(
            {"messages": [HumanMessage(content=prompt)]}
        )
        _raise_if_cancelled(runtime)
        technical_plan = TechnicalPlan.model_validate(result.get("structured_response"))
        _raise_if_cancelled(runtime)
        final_result = ArchHypo(
            uncertainty=state["uncertainty"],
            hypothesis=hypothesis,
            classification=classification,
            technical_plan=technical_plan,
        )
        return {
            "technical_plan": technical_plan,
            "result": final_result,
            "messages": [_agent_message("technical_plan_agent", technical_plan)],
        }

    return create_technical_plan


def _raise_if_cancelled(runtime: Runtime[RunContext] | None) -> None:
    """Stop the graph before a cancelled node writes another checkpoint."""

    control = getattr(runtime, "control", None)
    if control is not None and control.drain_requested:
        raise AgentCancelledError(control.drain_reason or "client_cancelled")


def _agent_message(name: str, value: object) -> AIMessage:
    """Append one structured agent result to the graph message history."""

    model_dump_json = getattr(value, "model_dump_json", None)
    if not callable(model_dump_json):
        raise TypeError(f"{name} did not return a Pydantic model")
    return AIMessage(name=name, content=model_dump_json(indent=2))


__all__ = [
    "Node",
    "create_classify_hypothesis_node",
    "create_formulate_hypothesis_node",
    "create_technical_plan_node",
]
