"""Conversation records returned by the application service."""

from dataclasses import dataclass, field
from typing import Literal

from archhypo_flow_agent.core import ToolCallRecord


@dataclass(frozen=True, slots=True)
class ConversationMessage:
    role: Literal["user", "assistant"]
    content: str
    tool_calls: list[ToolCallRecord] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ConversationSummary:
    thread_id: str
    title: str
    message_count: int
    updated_at: str
    pinned: bool
    project_id: str | None
    preview: str


@dataclass(frozen=True, slots=True)
class Conversation:
    thread_id: str
    title: str
    message_count: int
    updated_at: str
    pinned: bool
    project_id: str | None
    preview: str
    messages: list[ConversationMessage]
    pending_hypothesis_review: dict[str, object] | None = None


__all__ = ["Conversation", "ConversationMessage", "ConversationSummary"]
