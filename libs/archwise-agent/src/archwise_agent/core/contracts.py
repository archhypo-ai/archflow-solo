"""Small contracts shared by the orchestrator and services."""

from __future__ import annotations

class AgentCancelledError(Exception):
    """Raised when a client requests cancellation of an active run."""


__all__ = ["AgentCancelledError"]
