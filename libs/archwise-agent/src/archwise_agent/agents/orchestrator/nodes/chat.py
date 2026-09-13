"""Nodes used by the initial conversational orchestrator."""

from __future__ import annotations

from collections.abc import Callable

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage

from archwise_agent.core import AgentState


Node = Callable[[AgentState], dict[str, list[BaseMessage]]]


def create_respond_node(model: BaseChatModel) -> Node:
    """Create the model-response node with an injected provider client."""

    def respond(state: AgentState) -> dict[str, list[BaseMessage]]:
        response = model.invoke(state["messages"])
        return {"messages": [response]}

    return respond


__all__ = ["Node", "create_respond_node"]
