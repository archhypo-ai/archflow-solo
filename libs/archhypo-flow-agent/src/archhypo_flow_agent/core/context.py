"""Runtime context passed to one graph execution."""

from typing import Literal, NotRequired, TypedDict


class AgentRunContext(TypedDict):
    """User and project context resolved when a chat turn starts."""

    global_context: str
    project_context: str
    project_id: NotRequired[str | None]
    language: NotRequired[Literal["en", "pt-BR"]]
    hitl_enabled: NotRequired[bool]


__all__ = ["AgentRunContext"]
