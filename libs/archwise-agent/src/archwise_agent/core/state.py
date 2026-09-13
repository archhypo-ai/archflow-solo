"""State contracts shared by ArchWise agent implementations."""

from operator import add
from typing import Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import NotRequired, TypedDict

from .contracts import AgentResult, WorkflowPhase


class AgentState(TypedDict):
    """Minimal conversational state for the first agent.

    The reducer keeps existing messages and appends new messages on every
    invocation of the same checkpoint thread.
    """

    messages: Annotated[list[AnyMessage], add_messages]
    phase: NotRequired[WorkflowPhase]
    agent_results: NotRequired[Annotated[list[AgentResult], add]]


__all__ = ["AgentState"]
