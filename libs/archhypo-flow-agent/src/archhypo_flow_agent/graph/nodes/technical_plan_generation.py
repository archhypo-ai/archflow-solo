"""Node that creates a short technical plan and the aggregate result."""

from langchain_core.language_models import BaseChatModel
from langgraph.runtime import Runtime

from archhypo_flow_agent.agents import build_technical_plan_generation_agent
from archhypo_flow_agent.agents.technical_plan_generation import SYSTEM_PROMPT
from archhypo_flow_agent.core import AgentRunContext, AgentState, ArchHypoResult

from .support import contextual_system_prompt


def create_technical_plan_generation_node(model: BaseChatModel):
    agent = build_technical_plan_generation_agent(model)

    def plan(
        state: AgentState,
        runtime: Runtime[AgentRunContext] | None = None,
    ) -> dict[str, object]:
        discovery = state.get("discovery")
        hypothesis = state.get("hypothesis")
        assessment = state.get("assessment")
        uncertainty = state.get("uncertainty")
        if (
            discovery is None
            or hypothesis is None
            or assessment is None
            or uncertainty is None
        ):
            raise ValueError(
                "discovery, hypothesis, and assessment are required to plan"
            )

        technical_plan = agent.invoke(
            {
                "system_prompt": contextual_system_prompt(SYSTEM_PROMPT, runtime),
                "material": (
                    f"Architectural uncertainty:\n{uncertainty}\n\n"
                    "Hypothesis:\n"
                    f"{hypothesis.model_dump_json(indent=2)}\n\n"
                    "Assessment:\n"
                    f"{assessment.model_dump_json(indent=2)}"
                ),
            }
        )
        result = ArchHypoResult(
            uncertainty=uncertainty,
            discovery=discovery,
            hypothesis=hypothesis,
            assessment=assessment,
            technical_plan=technical_plan,
        )
        return {"technical_plan": technical_plan, "result": result}

    return plan


__all__ = ["create_technical_plan_generation_node"]
