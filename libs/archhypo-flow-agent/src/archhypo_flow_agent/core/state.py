"""State shared by the initial conversational graph."""

from langgraph.graph import MessagesState


class AgentState(MessagesState):
    """Conversation message state; messages use LangGraph's add reducer."""


__all__ = ["AgentState"]
