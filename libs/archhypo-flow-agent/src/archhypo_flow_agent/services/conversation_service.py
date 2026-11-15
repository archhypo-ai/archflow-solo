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

from .chat_projection import legacy_review_approval_kind, message_text, project_messages
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

    def replace_graph(self, graph: Any) -> None:
        """Replace the graph while the owning service holds the shared lock."""
        self._graph = graph

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
                pending_hypothesis_review=_pending_review(
                    snapshot,
                    "hypothesis_review",
                ),
                pending_technical_plan_review=_pending_review(
                    snapshot,
                    "technical_plan_review",
                ),
                completed_reviews=_completed_reviews(snapshot),
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


def _pending_review(snapshot: Any, kind: str) -> dict[str, object] | None:
    for task in getattr(snapshot, "tasks", ()):
        for pending_interrupt in task.interrupts:
            payload = pending_interrupt.value
            if (
                isinstance(payload, dict)
                and payload.get("kind") == kind
            ):
                return payload
    return None


def _completed_reviews(snapshot: Any) -> list[dict[str, object]]:
    values = snapshot.values if isinstance(snapshot.values, dict) else {}
    history = values.get("review_history", [])
    completed = [
        record
        for record in history
        if isinstance(record, dict) and _review_was_approved(record)
    ] if isinstance(history, list) else []
    raw_messages = values.get("messages", [])
    messages = [
        message for message in raw_messages if isinstance(message, BaseMessage)
    ] if isinstance(raw_messages, list) else []

    if not completed:
        completed = _legacy_completed_reviews(values, messages)

    positioned: list[dict[str, object]] = []
    for record in completed:
        raw_position = record.get("after_message_count")
        if isinstance(raw_position, int):
            position = min(max(0, raw_position), len(messages))
            record = {
                **record,
                "after_message_count": len(project_messages(messages[:position])),
            }
        positioned.append(record)
    return sorted(
        positioned,
        key=lambda record: (
            record.get("after_message_count", 0),
            0 if record.get("kind") == "hypothesis_review" else 1,
        ),
    )


def _review_was_approved(record: dict[str, object]) -> bool:
    decision = record.get("decision")
    return (
        isinstance(decision, dict)
        and decision.get("decision") == "approved"
    )


def _legacy_completed_reviews(
    values: dict[str, object],
    messages: list[BaseMessage],
) -> list[dict[str, object]]:
    completed: list[dict[str, object]] = []
    hypothesis = values.get("hypothesis")
    hypothesis_decision = values.get("hypothesis_review")
    hypothesis_payload = _model_payload(hypothesis)
    decision_payload = _model_payload(hypothesis_decision)
    if (
        hypothesis_payload is not None
        and decision_payload is not None
        and decision_payload.get("decision") == "approved"
    ):
        raw_position = _legacy_approval_position(messages, "hypothesis_review")
        completed.append(
            {
                "kind": "hypothesis_review",
                "review": {
                    "kind": "hypothesis_review",
                    "hypothesis": hypothesis_payload,
                },
                "decision": decision_payload,
                "after_message_count": raw_position,
            }
        )

    assessment_payload = _model_payload(values.get("assessment"))
    plan_payload = _model_payload(values.get("technical_plan"))
    plan_decision = _model_payload(values.get("technical_plan_review"))
    if (
        assessment_payload is not None
        and plan_payload is not None
        and plan_decision is not None
        and plan_decision.get("decision") == "approved"
    ):
        raw_position = _legacy_approval_position(messages, "technical_plan_review")
        completed.append(
            {
                "kind": "technical_plan_review",
                "review": {
                    "kind": "technical_plan_review",
                    "assessment": assessment_payload,
                    "technical_plan": plan_payload,
                },
                "decision": plan_decision,
                "after_message_count": raw_position,
            }
        )
    return completed


def _model_payload(value: object) -> dict[str, object] | None:
    if isinstance(value, dict):
        return value
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        payload = model_dump(mode="json")
        return payload if isinstance(payload, dict) else None
    return None


def _legacy_approval_position(messages: list[BaseMessage], kind: str) -> int:
    for index in range(len(messages) - 1, -1, -1):
        message = messages[index]
        if message.type == "human" and legacy_review_approval_kind(
            message_text(message)
        ) == kind:
            return index
    return len(messages)


__all__ = ["ConversationService"]
