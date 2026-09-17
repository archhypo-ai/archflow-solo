"""Application-facing service contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

from agent_stream_py import AgentEvent
from langchain_core.messages import AIMessage

from archwise_agent.core import ArchHypo

from .conversation_projection import message_text


@dataclass(frozen=True, slots=True)
class AgentTurn:
    """Assistant response and typed ArchHypo result for one turn."""

    thread_id: str
    message: AIMessage
    result: ArchHypo | None

    @property
    def text(self) -> str:
        return message_text(self.message)


AgentStreamEvent: TypeAlias = AgentEvent


@dataclass(frozen=True, slots=True)
class ConversationMessage:
    """User-visible message from a checkpointed conversation."""

    role: Literal["user", "assistant"]
    content: str


@dataclass(frozen=True, slots=True)
class ConversationSummary:
    """Metadata used to list available conversations."""

    thread_id: str
    title: str
    message_count: int
    pinned: bool = False


@dataclass(frozen=True, slots=True)
class Conversation:
    """Conversation metadata and its user-visible messages."""

    thread_id: str
    title: str
    message_count: int
    messages: list[ConversationMessage]
    pinned: bool = False


__all__ = [
    "AgentStreamEvent",
    "AgentTurn",
    "Conversation",
    "ConversationMessage",
    "ConversationSummary",
]
