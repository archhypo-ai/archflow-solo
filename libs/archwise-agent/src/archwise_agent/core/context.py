"""Execution identity shared by transports and graph nodes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import NotRequired
from uuid import uuid4

from typing_extensions import TypedDict

DEFAULT_WORKSPACE_ID = "default"


class RunContext(TypedDict, total=False):
    """Runtime-only context available to LangGraph nodes."""

    thread_id: NotRequired[str]
    workspace_id: NotRequired[str]
    project_id: NotRequired[str | None]
    user_id: NotRequired[str | None]
    run_id: NotRequired[str]


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    """Validated identity for one graph execution.

    ``thread_id`` remains the LangGraph checkpoint key. The other fields are
    runtime context and are intentionally not mixed into the message history.
    """

    thread_id: str
    workspace_id: str = DEFAULT_WORKSPACE_ID
    project_id: str | None = None
    user_id: str | None = None
    run_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        _require_value(self.thread_id, "thread_id")
        _require_value(self.workspace_id, "workspace_id")
        if self.project_id is not None:
            _require_value(self.project_id, "project_id")
        if self.user_id is not None:
            _require_value(self.user_id, "user_id")
        _require_value(self.run_id, "run_id")

    def as_graph_context(self) -> RunContext:
        """Return the context shape accepted by the compiled graph."""

        return {
            "thread_id": self.thread_id,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "user_id": self.user_id,
            "run_id": self.run_id,
        }


def _require_value(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} must not be empty")


__all__ = [
    "DEFAULT_WORKSPACE_ID",
    "ExecutionContext",
    "RunContext",
]
