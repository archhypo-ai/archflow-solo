"""Typed envelopes shared by the orchestrator and future subagents."""

from __future__ import annotations

from typing import Any, Literal

from typing_extensions import NotRequired, TypedDict

WorkflowPhase = Literal[
    "conversation",
    "intake",
    "analysis",
    "synthesis",
    "review",
    "completed",
    "failed",
]
AgentRunStatus = Literal["pending", "running", "completed", "failed", "skipped"]


class AgentCancelledError(Exception):
    """Raised when a client requests cancellation of an active run."""


class AgentResult(TypedDict):
    """Serializable result envelope returned by a subagent execution."""

    agent_name: str
    status: AgentRunStatus
    output: NotRequired[dict[str, Any]]
    error: NotRequired[str]


__all__ = [
    "AgentCancelledError",
    "AgentResult",
    "AgentRunStatus",
    "WorkflowPhase",
]
