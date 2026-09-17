"""Shared helpers for ArchWise workflow nodes."""

from __future__ import annotations

from collections.abc import Callable

from langchain_core.messages import AIMessage
from langgraph.runtime import Runtime

from archwise_agent.core import AgentCancelledError, ArchHypoState, RunContext

Node = Callable[
    [ArchHypoState, Runtime[RunContext] | None],
    dict[str, object],
]


def raise_if_cancelled(runtime: Runtime[RunContext] | None) -> None:
    """Stop the graph before a cancelled node writes another checkpoint."""

    control = getattr(runtime, "control", None)
    if control is not None and control.drain_requested:
        raise AgentCancelledError(control.drain_reason or "client_cancelled")


def agent_message(name: str, value: object) -> AIMessage:
    """Append one structured agent result to the internal graph history."""

    model_dump_json = getattr(value, "model_dump_json", None)
    if not callable(model_dump_json):
        raise TypeError(f"{name} did not return a Pydantic model")
    return AIMessage(name=name, content=model_dump_json(indent=2))


__all__ = ["Node", "agent_message", "raise_if_cancelled"]
