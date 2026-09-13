"""Application-facing service for the ArchWise agent."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any, Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.checkpoint.base import BaseCheckpointSaver

from archwise_agent.agents import build_archwise_agent
from archwise_agent.config import AgentSettings
from archwise_agent.core import DEFAULT_WORKSPACE_ID, ExecutionContext
from archwise_agent.persistence import (
    CHECKPOINT_DB_PATH,
    SQLitePersistence,
    open_sqlite_persistence,
)

from .conversation_service import ConversationService


@dataclass(frozen=True, slots=True)
class AgentTurn:
    """Assistant response returned by one agent turn."""

    thread_id: str
    message: AIMessage

    @property
    def text(self) -> str:
        return _message_text(self.message)


@dataclass(frozen=True, slots=True)
class AgentStreamEvent:
    """Transport-neutral event emitted while an agent turn is running."""

    kind: Literal["phase", "delta", "done"]
    thread_id: str
    phase: str | None = None
    text: str | None = None


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


class AgentService:
    """Keep the compiled agent alive and provide a stable application API."""

    def __init__(
        self,
        *,
        configuration: AgentSettings | None = None,
        model: BaseChatModel | None = None,
        checkpointer: BaseCheckpointSaver | None = None,
        database_path: Path | None = None,
    ) -> None:
        self._lock = RLock()
        self._persistence: SQLitePersistence | None = None
        self._conversation_service: ConversationService | None = None

        if checkpointer is None:
            self._persistence = open_sqlite_persistence(
                database_path or CHECKPOINT_DB_PATH
            )
            self._conversation_service = ConversationService(
                self._persistence.conversations
            )
            active_checkpointer = self._persistence.checkpointer
        else:
            active_checkpointer = checkpointer

        try:
            self._agent = build_archwise_agent(
                model=model,
                configuration=configuration,
                checkpointer=active_checkpointer,
            )
        except Exception:
            self.close()
            raise

    def send(
        self,
        *,
        thread_id: str,
        message: str,
        workspace_id: str = DEFAULT_WORKSPACE_ID,
        project_id: str | None = None,
        user_id: str | None = None,
    ) -> AgentTurn:
        """Send a message while preserving thread and execution context."""

        if not thread_id.strip():
            raise ValueError("thread_id must not be empty")
        if not message.strip():
            raise ValueError("message must not be empty")
        context = ExecutionContext(
            thread_id=thread_id,
            workspace_id=workspace_id,
            project_id=project_id,
            user_id=user_id,
        )

        with self._lock:
            if self._conversation_service is not None:
                self._conversation_service.ensure(thread_id, message)

            result: dict[str, Any] = self._agent.invoke(
                {"messages": [HumanMessage(content=message)]},
                {"configurable": {"thread_id": thread_id}},
                context=context.as_graph_context(),
            )
            response = result["messages"][-1]
            if not isinstance(response, AIMessage):
                raise TypeError("agent did not return an AI message")

            if self._conversation_service is not None:
                self._conversation_service.ensure(thread_id)

        return AgentTurn(thread_id=thread_id, message=response)

    def stream(
        self,
        *,
        thread_id: str,
        message: str,
        workspace_id: str = DEFAULT_WORKSPACE_ID,
        project_id: str | None = None,
        user_id: str | None = None,
    ) -> Iterator[AgentStreamEvent]:
        """Stream one agent turn as phases and text deltas."""

        if not thread_id.strip():
            raise ValueError("thread_id must not be empty")
        if not message.strip():
            raise ValueError("message must not be empty")
        context = ExecutionContext(
            thread_id=thread_id,
            workspace_id=workspace_id,
            project_id=project_id,
            user_id=user_id,
        )

        if self._conversation_service is not None:
            self._conversation_service.ensure(thread_id, message)

        yield AgentStreamEvent(
            kind="phase",
            thread_id=thread_id,
            phase="thinking",
        )

        streamed_text = False
        for item in self._agent.stream(
            {"messages": [HumanMessage(content=message)]},
            {"configurable": {"thread_id": thread_id}},
            context=context.as_graph_context(),
            stream_mode="messages",
        ):
            chunk = item[0] if isinstance(item, tuple) else item
            text = _message_chunk_text(chunk)
            if not text:
                continue

            if not streamed_text:
                yield AgentStreamEvent(
                    kind="phase",
                    thread_id=thread_id,
                    phase="answering",
                )
                streamed_text = True
            yield AgentStreamEvent(
                kind="delta",
                thread_id=thread_id,
                text=text,
            )

        if not streamed_text:
            state = self._agent.get_state(
                {"configurable": {"thread_id": thread_id}}
            )
            values = state.values if isinstance(state.values, dict) else {}
            messages = values.get("messages", [])
            if messages:
                text = _message_text(messages[-1])
                if text:
                    yield AgentStreamEvent(
                        kind="delta",
                        thread_id=thread_id,
                        text=text,
                    )

        if self._conversation_service is not None:
            self._conversation_service.ensure(thread_id)

        yield AgentStreamEvent(kind="done", thread_id=thread_id)

    def list_conversations(self) -> list[ConversationSummary]:
        """List latest checkpoint state for every known thread."""

        with self._lock:
            latest: dict[str, Any] = {}
            for item in self._agent.checkpointer.list(None):
                thread_id = _thread_id_from_checkpoint(item)
                if not thread_id:
                    continue
                current = latest.get(thread_id)
                if current is None or _checkpoint_key(item) > _checkpoint_key(
                    current
                ):
                    latest[thread_id] = item

            metadata = (
                {
                    item.thread_id: item
                    for item in self._conversation_service.list()
                }
                if self._conversation_service is not None
                else {}
            )
            conversations = [
                _conversation_summary(
                    thread_id,
                    _messages_from_checkpoint(item),
                    title=metadata.get(thread_id).title
                    if thread_id in metadata
                    else None,
                    pinned=metadata.get(thread_id).pinned
                    if thread_id in metadata
                    else False,
                )
                for thread_id, item in latest.items()
            ]
            return sorted(conversations, key=lambda item: item.title.casefold())

    def get_conversation(self, thread_id: str) -> Conversation | None:
        """Load one conversation from its checkpoint thread."""

        if not thread_id.strip():
            raise ValueError("thread_id must not be empty")

        with self._lock:
            state = self._agent.get_state(
                {"configurable": {"thread_id": thread_id}}
            )
            values = state.values if isinstance(state.values, dict) else {}
            messages = values.get("messages", [])
            if not messages:
                return None

            metadata = (
                self._conversation_service.get(thread_id)
                if self._conversation_service is not None
                else None
            )
            conversation = _conversation_summary(
                thread_id,
                messages,
                title=metadata.title if metadata is not None else None,
                pinned=metadata.pinned if metadata is not None else False,
            )
            return Conversation(
                thread_id=conversation.thread_id,
                title=conversation.title,
                message_count=conversation.message_count,
                messages=_conversation_messages(messages),
                pinned=conversation.pinned,
            )

    def update_conversation(
        self,
        thread_id: str,
        *,
        title: str | None = None,
        pinned: bool | None = None,
    ) -> ConversationSummary | None:
        """Update metadata for an existing checkpointed conversation."""

        if not thread_id.strip():
            raise ValueError("thread_id must not be empty")
        if self._conversation_service is None:
            return None

        with self._lock:
            metadata = self._conversation_service.update(
                thread_id,
                title=title,
                pinned=pinned,
            )
            if metadata is None:
                return None

            state = self._agent.get_state(
                {"configurable": {"thread_id": thread_id}}
            )
            values = state.values if isinstance(state.values, dict) else {}
            messages = values.get("messages", [])
            return _conversation_summary(
                thread_id,
                list(messages),
                title=metadata.title,
                pinned=metadata.pinned,
            )

    def delete_conversation(self, thread_id: str) -> bool:
        """Delete a thread checkpoint and its local conversation metadata."""

        if not thread_id.strip():
            raise ValueError("thread_id must not be empty")

        with self._lock:
            state = self._agent.get_state(
                {"configurable": {"thread_id": thread_id}}
            )
            has_checkpoint = bool(state.values)
            has_metadata = (
                self._conversation_service is not None
                and self._conversation_service.get(thread_id) is not None
            )
            if not has_checkpoint and not has_metadata:
                return False

            if self._persistence is not None:
                self._persistence.delete_thread(thread_id)
            else:
                self._agent.checkpointer.delete_thread(thread_id)
            return True

    @property
    def agent(self):
        """Expose the compiled agent to future streaming/resume adapters."""

        return self._agent

    def close(self) -> None:
        """Close resources owned by the default SQLite checkpointer."""

        with self._lock:
            if self._persistence is not None:
                self._persistence.close()
                self._persistence = None
                self._conversation_service = None


def _thread_id_from_checkpoint(checkpoint: Any) -> str | None:
    config = getattr(checkpoint, "config", {})
    configurable = config.get("configurable", {}) if isinstance(config, dict) else {}
    thread_id = configurable.get("thread_id")
    return thread_id if isinstance(thread_id, str) else None


def _checkpoint_key(checkpoint: Any) -> str:
    values = getattr(checkpoint, "checkpoint", {})
    if not isinstance(values, dict):
        return ""
    return str(values.get("ts", values.get("id", "")))


def _messages_from_checkpoint(checkpoint: Any) -> list[Any]:
    values = getattr(checkpoint, "checkpoint", {})
    if not isinstance(values, dict):
        return []
    channels = values.get("channel_values", {})
    if not isinstance(channels, dict):
        return []
    messages = channels.get("messages", [])
    return list(messages) if isinstance(messages, list) else []


def _conversation_summary(
    thread_id: str,
    messages: list[Any],
    *,
    title: str | None = None,
    pinned: bool = False,
) -> ConversationSummary:
    title = title or next(
        (
            _message_text(message)
            for message in messages
            if _message_role(message) == "user" and _message_text(message)
        ),
        "Untitled conversation",
    )
    return ConversationSummary(
        thread_id=thread_id,
        title=_truncate(title),
        message_count=len(messages),
        pinned=pinned,
    )


def _conversation_messages(messages: list[Any]) -> list[ConversationMessage]:
    result: list[ConversationMessage] = []
    for message in messages:
        role = _message_role(message)
        text = _message_text(message)
        if role in ("user", "assistant") and text:
            result.append(ConversationMessage(role=role, content=text))
    return result


def _message_role(message: Any) -> Literal["user", "assistant"] | None:
    if isinstance(message, HumanMessage) or getattr(message, "type", None) == "human":
        return "user"
    if isinstance(message, AIMessage) or getattr(message, "type", None) == "ai":
        return "assistant"
    return None


def _message_chunk_text(message: BaseMessage | Any) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                text = block.get("text") or block.get("content")
                if isinstance(text, str):
                    parts.append(text)
        return "".join(parts)
    return str(content) if content else ""


def _message_text(message: BaseMessage | Any) -> str:
    return _message_chunk_text(message).strip()


def _truncate(value: str, limit: int = 60) -> str:
    return value if len(value) <= limit else f"{value[: limit - 1].rstrip()}…"


__all__ = [
    "AgentService",
    "AgentStreamEvent",
    "AgentTurn",
    "Conversation",
    "ConversationMessage",
    "ConversationSummary",
]
