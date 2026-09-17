"""Application-facing service for the ArchWise agent."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any, Literal, TypeAlias

from agent_stream_py import (
    AgentEvent,
    cancelled_event,
    done_event,
    phase_event,
    text_delta_event,
)
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.runtime import RunControl

from archwise_agent.agents import build_archwise_agent
from archwise_agent.config import AgentSettings, settings
from archwise_agent.core import (
    DEFAULT_WORKSPACE_ID,
    AgentCancelledError,
    ArchHypo,
    ExecutionContext,
)
from archwise_agent.observability import build_observability
from archwise_agent.persistence import (
    CHECKPOINT_DB_PATH,
    SQLitePersistence,
    open_sqlite_persistence,
)

from .conversation_service import ConversationService


@dataclass(frozen=True, slots=True)
class AgentTurn:
    """Assistant response and typed ArchHypo result for one turn."""

    thread_id: str
    message: AIMessage
    result: ArchHypo | None

    @property
    def text(self) -> str:
        return _message_text(self.message)


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
        self._configuration = configuration or (
            settings if model is None else AgentSettings(_env_file=None)
        )
        self._observability = build_observability(self._configuration)
        self._active_runs: dict[str, RunControl] = {}
        self._run_threads: dict[str, str] = {}
        self._deleting_threads: set[str] = set()
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
                configuration=self._configuration,
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
        run_id: str | None = None,
    ) -> AgentTurn:
        """Run one cancellable graph execution for a conversation thread."""

        _validate_input(thread_id, message)
        context = ExecutionContext(
            thread_id=thread_id,
            workspace_id=workspace_id,
            project_id=project_id,
            user_id=user_id,
            **({"run_id": run_id} if run_id is not None else {}),
        )
        control = RunControl()
        self._register_run(context, control, message)

        try:
            if control.drain_requested:
                raise AgentCancelledError(control.drain_reason or "client_cancelled")

            graph_config = self._observability.graph_config(context)
            graph_config["configurable"] = {"thread_id": thread_id}
            state: dict[str, Any] = self._agent.invoke(
                {
                    "uncertainty": message,
                    "messages": [HumanMessage(content=message)],
                },
                graph_config,
                context=context.as_graph_context(),
                control=control,
            )
            if control.drain_requested:
                raise AgentCancelledError(control.drain_reason or "client_cancelled")

            direct_response = state.get("response")
            if isinstance(direct_response, str) and direct_response.strip():
                result = state.get("result")
                archhypo = _archhypo_from_value(result) if result is not None else None
                response = AIMessage(content=direct_response)
            else:
                archhypo = _archhypo_from_value(state.get("result"))
                response = _response_message(archhypo)

            if self._conversation_service is not None:
                with self._lock:
                    self._conversation_service.ensure(thread_id)

            return AgentTurn(thread_id=thread_id, message=response, result=archhypo)
        finally:
            self._finish_run(context.run_id)

    def _register_run(
        self,
        context: ExecutionContext,
        control: RunControl,
        message: str,
    ) -> None:
        """Register a run before work starts and persist its initial metadata."""

        with self._lock:
            if context.run_id in self._active_runs:
                raise ValueError("run_id is already active")
            self._active_runs[context.run_id] = control
            self._run_threads[context.run_id] = context.thread_id
            try:
                if self._conversation_service is not None:
                    self._conversation_service.ensure(context.thread_id, message)
            except Exception:
                self._active_runs.pop(context.run_id, None)
                self._run_threads.pop(context.run_id, None)
                raise

    def _finish_run(self, run_id: str) -> None:
        """Release a run registration and wake deletion waiters."""

        with self._lock:
            self._active_runs.pop(run_id, None)
            thread_id = self._run_threads.pop(run_id, None)
            if (
                thread_id is not None
                and thread_id in self._deleting_threads
                and not any(
                    active_thread_id == thread_id
                    for active_thread_id in self._run_threads.values()
                )
            ):
                self._delete_thread_storage(thread_id)
                self._deleting_threads.discard(thread_id)

    def stream(
        self,
        *,
        thread_id: str,
        message: str,
        workspace_id: str = DEFAULT_WORKSPACE_ID,
        project_id: str | None = None,
        user_id: str | None = None,
        run_id: str | None = None,
    ) -> Iterator[AgentStreamEvent]:
        """Run the simple graph and emit its final structured result."""

        _validate_input(thread_id, message)
        context = ExecutionContext(
            thread_id=thread_id,
            workspace_id=workspace_id,
            project_id=project_id,
            user_id=user_id,
            **({"run_id": run_id} if run_id is not None else {}),
        )
        control = RunControl()
        self._register_run(context, control, message)

        try:
            yield phase_event(
                thread_id=thread_id,
                run_id=context.run_id,
                phase="thinking",
            )
            if control.drain_requested:
                raise AgentCancelledError(control.drain_reason or "client_cancelled")

            graph_config = self._observability.graph_config(context)
            graph_config["configurable"] = {"thread_id": thread_id}
            state: dict[str, Any] = self._agent.invoke(
                {
                    "uncertainty": message,
                    "messages": [HumanMessage(content=message)],
                },
                graph_config,
                context=context.as_graph_context(),
                control=control,
            )
            if control.drain_requested:
                raise AgentCancelledError(control.drain_reason or "client_cancelled")

            direct_response = state.get("response")
            if isinstance(direct_response, str) and direct_response.strip():
                response_text = direct_response
            else:
                response_text = _archhypo_from_value(
                    state.get("result")
                ).model_dump_json(indent=2)

            yield phase_event(
                thread_id=thread_id,
                run_id=context.run_id,
                phase="answering",
            )
            yield text_delta_event(
                thread_id=thread_id,
                run_id=context.run_id,
                text=response_text,
            )

            if self._conversation_service is not None:
                self._conversation_service.ensure(thread_id)
            yield done_event(thread_id=thread_id, run_id=context.run_id)
        except AgentCancelledError as error:
            yield cancelled_event(
                thread_id=thread_id,
                run_id=context.run_id,
                reason=str(error),
            )
        finally:
            self._finish_run(context.run_id)

    def cancel_run(self, run_id: str) -> bool:
        """Request cooperative cancellation for one active agent run."""

        if not run_id.strip():
            raise ValueError("run_id must not be empty")
        with self._lock:
            control = self._active_runs.get(run_id)
        if control is None:
            return False
        control.request_drain("client_cancelled")
        return True

    def list_conversations(self) -> list[ConversationSummary]:
        """List latest checkpoint state for every known thread."""

        with self._lock:
            latest: dict[str, Any] = {}
            for item in self._agent.checkpointer.list(None):
                thread_id = _thread_id_from_checkpoint(item)
                if not thread_id:
                    continue
                current = latest.get(thread_id)
                if current is None or _checkpoint_key(item) > _checkpoint_key(current):
                    latest[thread_id] = item

            metadata = (
                {item.thread_id: item for item in self._conversation_service.list()}
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
                if thread_id not in self._deleting_threads
            ]
            return sorted(conversations, key=lambda item: item.title.casefold())

    def get_conversation(self, thread_id: str) -> Conversation | None:
        """Load one conversation from its checkpoint thread."""

        if not thread_id.strip():
            raise ValueError("thread_id must not be empty")

        with self._lock:
            if thread_id in self._deleting_threads:
                return None
            state = self._agent.get_state({"configurable": {"thread_id": thread_id}})
            values = state.values if isinstance(state.values, dict) else {}
            messages = _messages_from_values(values)
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
            if thread_id in self._deleting_threads:
                return None
            metadata = self._conversation_service.update(
                thread_id,
                title=title,
                pinned=pinned,
            )
            if metadata is None:
                return None

            state = self._agent.get_state({"configurable": {"thread_id": thread_id}})
            values = state.values if isinstance(state.values, dict) else {}
            messages = _messages_from_values(values)
            return _conversation_summary(
                thread_id,
                messages,
                title=metadata.title,
                pinned=metadata.pinned,
            )

    def delete_conversation(self, thread_id: str) -> bool:
        """Cancel active work and delete the thread when the run finishes."""

        if not thread_id.strip():
            raise ValueError("thread_id must not be empty")

        with self._lock:
            active_controls = [
                self._active_runs[run_id]
                for run_id, active_thread_id in self._run_threads.items()
                if active_thread_id == thread_id
            ]
            if active_controls:
                self._deleting_threads.add(thread_id)
                for control in active_controls:
                    control.request_drain("conversation_deleted")
                return True

            state = self._agent.get_state({"configurable": {"thread_id": thread_id}})
            has_checkpoint = bool(state.values)
            has_metadata = (
                self._conversation_service is not None
                and self._conversation_service.get(thread_id) is not None
            )
            if not has_checkpoint and not has_metadata:
                return False

            self._delete_thread_storage(thread_id)
            return True

    def _delete_thread_storage(self, thread_id: str) -> None:
        """Delete checkpoint and conversation metadata while holding the lock."""

        if self._persistence is not None:
            self._persistence.delete_thread(thread_id)
        else:
            self._agent.checkpointer.delete_thread(thread_id)

    @property
    def agent(self):
        """Expose the compiled agent to future streaming/resume adapters."""

        return self._agent

    def close(self) -> None:
        """Close resources owned by the default SQLite checkpointer."""

        with self._lock:
            self._observability.close()
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
    checkpoint_values = getattr(checkpoint, "checkpoint", {})
    if not isinstance(checkpoint_values, dict):
        return []
    channels = checkpoint_values.get("channel_values", {})
    return _messages_from_values(channels)


def _messages_from_values(values: dict[str, Any]) -> list[Any]:
    existing_messages = values.get("messages")
    if isinstance(existing_messages, list) and existing_messages:
        return _user_visible_messages(existing_messages)

    uncertainty = values.get("uncertainty")
    if not isinstance(uncertainty, str) or not uncertainty.strip():
        return []

    messages: list[Any] = [HumanMessage(content=uncertainty)]
    try:
        messages.append(_response_message(_archhypo_from_value(values.get("result"))))
    except TypeError:
        pass
    return messages


def _user_visible_messages(messages: list[Any]) -> list[Any]:
    """Hide internal workflow messages from the conversation API."""

    has_final_response = any(
        isinstance(message, AIMessage)
        and getattr(message, "name", None) == "response_agent"
        for message in messages
    )
    if has_final_response:
        return [
            message
            for message in messages
            if isinstance(message, HumanMessage)
            or (
                isinstance(message, AIMessage)
                and getattr(message, "name", None) == "response_agent"
            )
        ]

    return [message for message in messages if not _is_internal_message(message)]


def _is_internal_message(message: Any) -> bool:
    """Recognize workflow messages from checkpoints created before response."""

    name = getattr(message, "name", None)
    if name in {"hypothesis_agent", "classifier_agent", "technical_plan_agent"}:
        return True

    text = _message_text(message)
    return "{input}" in text and "{/input}" in text


def _archhypo_from_value(value: Any) -> ArchHypo:
    if isinstance(value, ArchHypo):
        return value
    if isinstance(value, dict):
        return ArchHypo.model_validate(value)
    raise TypeError("graph did not return an ArchHypo result")


def _response_message(archhypo: ArchHypo) -> AIMessage:
    return AIMessage(content=archhypo.model_dump_json(indent=2))


def _validate_input(thread_id: str, message: str) -> None:
    if not thread_id.strip():
        raise ValueError("thread_id must not be empty")
    if not message.strip():
        raise ValueError("message must not be empty")


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
