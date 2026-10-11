"""Small contracts shared by the orchestrator and services."""

from __future__ import annotations


class AgentCancelledError(Exception):
    """Raised when a client requests cancellation of an active run."""


class ConcurrentRunError(RuntimeError):
    """Raised when a conversation already has an active graph execution."""


__all__ = ["AgentCancelledError", "ConcurrentRunError"]
