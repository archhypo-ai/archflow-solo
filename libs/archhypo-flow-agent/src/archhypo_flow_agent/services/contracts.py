"""Conversation records returned by the application service."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class ConversationMessage:
    role: Literal["user", "assistant"]
    content: str


@dataclass(frozen=True, slots=True)
class ConversationSummary:
    thread_id: str
    title: str
    message_count: int
    updated_at: str


@dataclass(frozen=True, slots=True)
class Conversation:
    thread_id: str
    title: str
    message_count: int
    updated_at: str
    messages: list[ConversationMessage]


__all__ = ["Conversation", "ConversationMessage", "ConversationSummary"]
