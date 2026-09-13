"""Nodes used by the initial conversational orchestrator."""

from __future__ import annotations

from collections.abc import Callable

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langgraph.runtime import Runtime

from archwise_agent.core import AgentCancelledError, AgentState, RunContext


Node = Callable[[AgentState, Runtime[RunContext]], dict[str, list[BaseMessage]]]


def create_respond_node(model: BaseChatModel) -> Node:
    """Create the model-response node with an injected provider client."""

    def respond(
        state: AgentState,
        runtime: Runtime[RunContext],
    ) -> dict[str, list[BaseMessage]]:
        response: AIMessageChunk | None = None
        model_stream = model.stream(state["messages"])
        try:
            for chunk in model_stream:
                if runtime.control is not None and runtime.control.drain_requested:
                    reason = runtime.control.drain_reason or "client_cancelled"
                    raise AgentCancelledError(reason)

                response = chunk if response is None else response + chunk
        finally:
            close_stream = getattr(model_stream, "close", None)
            if callable(close_stream):
                close_stream()

        if response is None:
            raise RuntimeError("model produced no response")

        return {
            "messages": [
                AIMessage(
                    content=response.content,
                    additional_kwargs=response.additional_kwargs,
                    response_metadata=response.response_metadata,
                    id=response.id,
                    name=response.name,
                    tool_calls=response.tool_calls,
                    invalid_tool_calls=response.invalid_tool_calls,
                    usage_metadata=response.usage_metadata,
                )
            ]
        }

    return respond


__all__ = ["Node", "create_respond_node"]
