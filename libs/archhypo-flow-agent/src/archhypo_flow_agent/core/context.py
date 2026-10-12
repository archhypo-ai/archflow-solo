"""Runtime context passed to one graph execution."""

from typing import TypedDict


class AgentRunContext(TypedDict):
    """User and project context resolved when a chat turn starts."""

    global_context: str
    project_context: str


__all__ = ["AgentRunContext"]
