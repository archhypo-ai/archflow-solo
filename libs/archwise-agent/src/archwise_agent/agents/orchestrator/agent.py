"""Main ArchWise orchestrator."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from archwise_agent.config import AgentSettings
from archwise_agent.core import AgentState, RunContext
from archwise_agent.providers import create_openrouter_model

from .nodes import create_respond_node


def build_archwise_agent(
    *,
    model: BaseChatModel | None = None,
    configuration: AgentSettings | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
):
    """Build and compile the initial ArchWise orchestrator.

    The orchestrator currently has one conversational node. Future nodes will
    delegate to independent subagents without changing the public builder or
    the checkpoint boundary. The low-level builder uses ``InMemorySaver`` when
    no checkpointer is supplied; application runtimes should inject their
    owned persistent checkpointer.
    """

    chat_model = (
        model
        if model is not None
        else create_openrouter_model(configuration)
    )

    workflow = StateGraph(AgentState, context_schema=RunContext)
    workflow.add_node("respond", create_respond_node(chat_model))
    workflow.add_edge(START, "respond")
    workflow.add_edge("respond", END)

    return workflow.compile(
        checkpointer=(
            checkpointer if checkpointer is not None else InMemorySaver()
        )
    )


__all__ = ["build_archwise_agent"]
