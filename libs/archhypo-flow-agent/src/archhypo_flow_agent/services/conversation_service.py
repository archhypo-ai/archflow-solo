"""Conversation metadata and checkpoint transcript operations."""

from threading import Lock
from typing import Any

from langchain_core.messages import BaseMessage

from archhypo_flow_agent.persistence.conversations import (
    ConversationMetadata,
    ConversationRepository,
)
from archhypo_flow_agent.persistence.projects import ProjectRepository
from archhypo_flow_agent.persistence.sqlite import SQLitePersistence

from .chat_projection import project_messages
from .contracts import Conversation, ConversationMessage, ConversationSummary


class ConversationService:
    """Manage conversation metadata and project checkpoint history."""

    def __init__(
        self,
        *,
        graph: Any,
        conversations: ConversationRepository | None,
        projects: ProjectRepository | None,
        persistence: SQLitePersistence | None,
        lock: Lock,
    ) -> None:
        self._graph = graph
        self._conversations = conversations
        self._projects = projects
        self._persistence = persistence
        self._lock = lock

    def list(self) -> list[ConversationSummary]:
        if self._conversations is None:
            return []
        with self._lock:
            return [self._summary(metadata) for metadata in self._conversations.list()]

    def get(self, thread_id: str) -> Conversation | None:
        if not thread_id.strip() or self._conversations is None:
            return None
        with self._lock:
            metadata = self._conversations.get(thread_id)
            if metadata is None:
                return None
            snapshot = self._graph.get_state(
                {"configurable": {"thread_id": thread_id}}
            )
            messages = self._messages_from_snapshot(snapshot)
            return Conversation(
                thread_id=thread_id,
                title=metadata.title,
                message_count=len(messages),
                updated_at=metadata.updated_at,
                pinned=metadata.pinned,
                project_id=metadata.project_id,
                preview=messages[-1].content if messages else "",
                messages=messages,
                pending_hypothesis_review=_pending_hypothesis_review(snapshot),
            )

    def update(
        self,
        thread_id: str,
        *,
        title: str | None = None,
        pinned: bool | None = None,
    ) -> ConversationSummary | None:
        if not thread_id.strip() or self._conversations is None:
            return None
        with self._lock:
            metadata = self._conversations.update(
                thread_id,
                title=title,
                pinned=pinned,
            )
            return self._summary(metadata) if metadata is not None else None

    def set_project(
        self,
        thread_id: str,
        project_id: str | None,
    ) -> ConversationSummary | None:
        if not thread_id.strip() or self._conversations is None:
            return None
        with self._lock:
            if project_id is not None and (
                self._projects is None or self._projects.get(project_id) is None
            ):
                raise LookupError("Project not found.")
            metadata = self._conversations.set_project(thread_id, project_id)
            return self._summary(metadata) if metadata is not None else None

    def delete(self, thread_id: str) -> bool:
        if not thread_id.strip() or self._persistence is None:
            return False
        with self._lock:
            return self._persistence.delete_thread(thread_id)

    def _summary(self, metadata: ConversationMetadata) -> ConversationSummary:
        messages = self._load_messages(metadata.thread_id)
        return ConversationSummary(
            thread_id=metadata.thread_id,
            title=metadata.title,
            message_count=len(messages),
            updated_at=metadata.updated_at,
            pinned=metadata.pinned,
            project_id=metadata.project_id,
            preview=messages[-1].content if messages else "",
        )

    def _load_messages(self, thread_id: str) -> list[ConversationMessage]:
        state = self._graph.get_state({"configurable": {"thread_id": thread_id}})
        return self._messages_from_snapshot(state)

    def _messages_from_snapshot(self, state: Any) -> list[ConversationMessage]:
        values = state.values if isinstance(state.values, dict) else {}
        raw_messages = values.get("messages", [])
        messages = [
            message for message in raw_messages if isinstance(message, BaseMessage)
        ]
        return project_messages(messages)


def _pending_hypothesis_review(snapshot: Any) -> dict[str, object] | None:
    for task in getattr(snapshot, "tasks", ()):
        for pending_interrupt in task.interrupts:
            payload = pending_interrupt.value
            if (
                isinstance(payload, dict)
                and payload.get("kind") == "hypothesis_review"
            ):
                return payload
    return None


__all__ = ["ConversationService"]
