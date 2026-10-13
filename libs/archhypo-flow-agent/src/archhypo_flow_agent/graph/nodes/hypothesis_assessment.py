"""Node that assesses NFR, impact, and uncertainty for one hypothesis."""

from langchain_core.language_models import BaseChatModel
from langgraph.runtime import Runtime

from archhypo_flow_agent.agents import build_hypothesis_assessment_agent
from archhypo_flow_agent.agents.hypothesis_assessment import SYSTEM_PROMPT
from archhypo_flow_agent.core import AgentRunContext, AgentState

from .support import contextual_system_prompt


def create_hypothesis_assessment_node(model: BaseChatModel):
    agent = build_hypothesis_assessment_agent(model)

    def assess(
        state: AgentState,
        runtime: Runtime[AgentRunContext] | None = None,
    ) -> dict[str, object]:
        hypothesis = state.get("hypothesis")
        uncertainty = state.get("uncertainty")
        if hypothesis is None or uncertainty is None:
            raise ValueError(
                "hypothesis and uncertainty are required before assessment"
            )

        assessment = agent.invoke(
            {
                "system_prompt": contextual_system_prompt(SYSTEM_PROMPT, runtime),
                "material": (
                    f"Architectural uncertainty:\n{uncertainty}\n\n"
                    "Hypothesis:\n"
                    f"{hypothesis.model_dump_json(indent=2)}"
                ),
            }
        )
        return {"assessment": assessment}

    return assess


__all__ = ["create_hypothesis_assessment_node"]
