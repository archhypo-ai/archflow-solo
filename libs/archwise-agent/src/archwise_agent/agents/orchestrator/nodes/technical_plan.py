"""Technical-plan workflow node."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage
from langchain_core.runnables import Runnable
from langgraph.runtime import Runtime

from archwise_agent.core import ArchHypo, ArchHypoState, RunContext, TechnicalPlan
from archwise_agent.graph import GraphNode, agent_message, raise_if_cancelled


def create_technical_plan_node(
    technical_plan_agent: Runnable[Any, Any],
) -> GraphNode[ArchHypoState, RunContext]:
    """Create the node that generates the technical plan."""

    def create_technical_plan(
        state: ArchHypoState,
        runtime: Runtime[RunContext] | None = None,
    ) -> dict[str, object]:
        raise_if_cancelled(runtime)
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
        child_config = None
        if runtime is not None and isinstance(runtime.context, dict):
            child_config = {
                "configurable": {
                    "run_id": runtime.context.get("run_id"),
                    "thread_id": runtime.context.get("thread_id"),
                }
            }
        result = technical_plan_agent.invoke(
            {"messages": [HumanMessage(content=prompt)]},
            child_config,
            context=(runtime.context if runtime is not None else None),
        )
        raise_if_cancelled(runtime)
        technical_plan = TechnicalPlan.model_validate(result.get("structured_response"))
        raise_if_cancelled(runtime)
        final_result = ArchHypo(
            uncertainty=state["uncertainty"],
            hypothesis=hypothesis,
            classification=classification,
            technical_plan=technical_plan,
        )
        return {
            "technical_plan": technical_plan,
            "result": final_result,
            "messages": [agent_message("technical_plan_agent", technical_plan)],
        }

    return create_technical_plan


__all__ = ["create_technical_plan_node"]
