"""Node that extracts one architectural uncertainty from the conversation."""

from langchain_core.language_models import BaseChatModel
from langgraph.runtime import Runtime

from archhypo_flow_agent.agents import build_architectural_uncertainty_discovery_agent
from archhypo_flow_agent.agents.architectural_uncertainty_discovery import (
    SYSTEM_PROMPT,
)
from archhypo_flow_agent.core import AgentRunContext, AgentState

from .support import contextual_system_prompt, latest_user_input


def create_architectural_uncertainty_discovery_node(model: BaseChatModel):
    agent = build_architectural_uncertainty_discovery_agent(model)

    def discover(
        state: AgentState,
        runtime: Runtime[AgentRunContext] | None = None,
    ) -> dict[str, object]:
        report = agent.invoke(
            {
                "messages": state["messages"],
                "system_prompt": contextual_system_prompt(SYSTEM_PROMPT, runtime),
            }
        )
        uncertainty = report.uncertainty or latest_user_input(state["messages"])
        return {"discovery": report, "uncertainty": uncertainty}

    return discover


__all__ = ["create_architectural_uncertainty_discovery_node"]
