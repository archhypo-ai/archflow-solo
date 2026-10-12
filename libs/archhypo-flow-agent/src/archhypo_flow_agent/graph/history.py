"""Checkpoint reader graph used when no chat model is configured."""

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from archhypo_flow_agent.core import AgentState


def build_history_graph(checkpointer: BaseCheckpointSaver):
    """Compile a no-op graph so saved message state remains readable offline."""

    workflow = StateGraph(AgentState)
    workflow.add_node("checkpoint_reader", lambda _state: {})
    workflow.add_edge(START, "checkpoint_reader")
    workflow.add_edge("checkpoint_reader", END)
    return workflow.compile(checkpointer=checkpointer)


__all__ = ["build_history_graph"]
