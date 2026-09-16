"""ArchHypo orchestrator."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from archwise_agent.agents.hypothesis import build_hypothesis_agent
from archwise_agent.config import AgentSettings
from archwise_agent.core import AgentState, RunContext
from archwise_agent.providers import create_openrouter_model


def build_archwise_agent(
    *,
    model: BaseChatModel | None = None,
    configuration: AgentSettings | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
):
    """Build the ArchHypo orchestrator with its first workflow node.

    The parent graph owns conversation memory. The hypothesis agent is added
    as the first independent node so later NFR and planning agents can be
    appended without replacing the orchestration boundary.
    """

    chat_model = (
        model
        if model is not None
        else create_openrouter_model(configuration)
    )
    hypothesis_agent = build_hypothesis_agent(chat_model)
    workflow = StateGraph(AgentState, context_schema=RunContext)
    workflow.add_node("hypothesis_agent", hypothesis_agent)
    workflow.add_edge(START, "hypothesis_agent")
    workflow.add_edge("hypothesis_agent", END)

    return workflow.compile(
        checkpointer=(
            checkpointer if checkpointer is not None else InMemorySaver()
        )
    )


__all__ = ["build_archwise_agent"]
