"""Minimal LangGraph workflow for conversational responses."""

from collections.abc import Sequence

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from archhypo_flow_agent.agents import build_response_generation_agent
from archhypo_flow_agent.core import AgentState


def build_graph(
    model: BaseChatModel,
    *,
    tools: Sequence[BaseTool] = (),
    checkpointer: BaseCheckpointSaver | None = None,
):
    """Build ``START -> response_generation -> END``.

    The response-generation node wraps a LangChain ReAct agent. A checkpointer
    may be injected by the application; graph construction owns no storage.
    """

    response_agent = build_response_generation_agent(
        model,
        tools=tools,
    )
    workflow = StateGraph(AgentState)
    workflow.add_node("response_generation", response_agent)
    workflow.add_edge(START, "response_generation")
    workflow.add_edge("response_generation", END)
    return workflow.compile(checkpointer=checkpointer)


__all__ = ["build_graph"]
