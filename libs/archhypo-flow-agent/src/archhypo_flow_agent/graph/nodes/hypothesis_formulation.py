"""Node that formulates one hypothesis from the selected uncertainty."""

from langchain_core.language_models import BaseChatModel
from langgraph.runtime import Runtime

from archhypo_flow_agent.agents import build_hypothesis_formulation_agent
from archhypo_flow_agent.agents.hypothesis_formulation import SYSTEM_PROMPT
from archhypo_flow_agent.core import AgentRunContext, AgentState

from .support import contextual_system_prompt


def create_hypothesis_formulation_node(model: BaseChatModel):
    agent = build_hypothesis_formulation_agent(model)

    def formulate(
        state: AgentState,
        runtime: Runtime[AgentRunContext] | None = None,
    ) -> dict[str, object]:
        uncertainty = state.get("uncertainty")
        discovery = state.get("discovery")
        feedback = state.get("hypothesis_feedback")
        if uncertainty is None or discovery is None:
            raise ValueError(
                "discovery and uncertainty are required before formulation"
            )

        material = (
            f"Selected architectural uncertainty:\n{uncertainty}\n\n"
            "Discovery result:\n"
            f"{discovery.model_dump_json(indent=2)}"
        )
        if feedback:
            previous = state.get("hypothesis")
            material += (
                "\n\nPrevious hypothesis:\n"
                f"{previous.model_dump_json(indent=2) if previous else 'Unavailable'}"
                "\n\nReviewer feedback (address this directly):\n"
                f"{feedback}"
            )

        hypothesis = agent.invoke(
            {
                "system_prompt": contextual_system_prompt(SYSTEM_PROMPT, runtime),
                "material": material,
            }
        )
        return {
            "hypothesis": hypothesis,
            "uncertainty": hypothesis.uncertainty,
            "hypothesis_feedback": None,
            "hypothesis_review": None,
        }

    return formulate


__all__ = ["create_hypothesis_formulation_node"]
