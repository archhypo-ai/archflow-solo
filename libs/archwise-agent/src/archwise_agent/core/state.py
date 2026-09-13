"""State contracts shared by ArchWise agent implementations."""

from typing import Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """Minimal conversational state for the first agent.

    The reducer keeps existing messages and appends new messages on every
    invocation of the same checkpoint thread.
    """

    messages: Annotated[list[AnyMessage], add_messages]


__all__ = ["AgentState"]
