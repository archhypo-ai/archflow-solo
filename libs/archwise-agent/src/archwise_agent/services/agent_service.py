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
from langchain_core.messages import AIMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.runtime import RunControl

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

from .conversation_projection import (
    archhypo_from_value,
    checkpoint_key,
    checkpoint_thread_id,
    message_role,
    message_text,
    messages_from_checkpoint,
    messages_from_values,
    response_message,
)
from .conversation_service import ConversationService
from .graph_runner import GraphRunner
from .run_registry import RunRegistry


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


class AgentService:
    """Coordinate graph execution, runs, persistence, and conversations."""

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
        self._runs = RunRegistry(self._lock)
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
            self._runner = GraphRunner(
                model=model,
                configuration=self._configuration,
                checkpointer=active_checkpointer,
                observability=self._observability,
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
        context = self._create_context(
            thread_id=thread_id,
            workspace_id=workspace_id,
            project_id=project_id,
            user_id=user_id,
            run_id=run_id,
        )
        control = RunControl()
        self._register_run(context, control, message)

        try:
            state = self._run_graph(context, control, message)
            return self._turn_from_state(thread_id, state)
        finally:
            self._finish_run(context.run_id)

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
        """Run one graph execution and emit protocol events."""

        _validate_input(thread_id, message)
        context = self._create_context(
            thread_id=thread_id,
            workspace_id=workspace_id,
            project_id=project_id,
            user_id=user_id,
            run_id=run_id,
        )
        control = RunControl()
        self._register_run(context, control, message)

        try:
            yield phase_event(
                thread_id=thread_id,
                run_id=context.run_id,
                phase="thinking",
            )
            state = self._run_graph(context, control, message)
            response_text = self._turn_from_state(thread_id, state).text

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
        return self._runs.cancel(run_id)

    def list_conversations(self) -> list[ConversationSummary]:
        """List latest checkpoint state for every known thread."""

        with self._lock:
            latest: dict[str, Any] = {}
            for item in self._runner.list_checkpoints():
                thread_id = checkpoint_thread_id(item)
                if not thread_id:
                    continue
                current = latest.get(thread_id)
                if current is None or checkpoint_key(item) > checkpoint_key(current):
                    latest[thread_id] = item

            metadata = self._conversation_metadata()
            conversations = [
                _conversation_summary(
                    thread_id,
                    messages_from_checkpoint(item),
                    title=(
                        metadata[thread_id].title if thread_id in metadata else None
                    ),
                    pinned=(
                        metadata[thread_id].pinned if thread_id in metadata else False
                    ),
                )
                for thread_id, item in latest.items()
                if not self._runs.is_deleting(thread_id)
            ]
            return sorted(conversations, key=lambda item: item.title.casefold())

    def get_conversation(self, thread_id: str) -> Conversation | None:
        """Load one conversation from its checkpoint thread."""

        if not thread_id.strip():
            raise ValueError("thread_id must not be empty")
        with self._lock:
            if self._runs.is_deleting(thread_id):
                return None
            state = self._runner.get_state(thread_id)
            values = state.values if isinstance(state.values, dict) else {}
            messages = messages_from_values(values)
            if not messages:
                return None

            metadata = self._metadata_for(thread_id)
            summary = _conversation_summary(
                thread_id,
                messages,
                title=metadata.title if metadata is not None else None,
                pinned=metadata.pinned if metadata is not None else False,
            )
            return Conversation(
                thread_id=summary.thread_id,
                title=summary.title,
                message_count=summary.message_count,
                messages=_conversation_messages(messages),
                pinned=summary.pinned,
            )

    def update_conversation(
        self,
        thread_id: str,
        *,
        title: str | None = None,
        pinned: bool | None = None,
    ) -> ConversationSummary | None:
        """Update mutable conversation metadata."""

        if not thread_id.strip():
            raise ValueError("thread_id must not be empty")
        if self._conversation_service is None:
            return None

        with self._lock:
            if self._runs.is_deleting(thread_id):
                return None
            metadata = self._conversation_service.update(
                thread_id,
                title=title,
                pinned=pinned,
            )
            if metadata is None:
                return None

            state = self._runner.get_state(thread_id)
            values = state.values if isinstance(state.values, dict) else {}
            messages = messages_from_values(values)
            return _conversation_summary(
                thread_id,
                messages,
                title=metadata.title,
                pinned=metadata.pinned,
            )

    def delete_conversation(self, thread_id: str) -> bool:
        """Cancel active work and delete the thread when it finishes."""

        if not thread_id.strip():
            raise ValueError("thread_id must not be empty")

        with self._lock:
            if self._runs.request_thread_deletion(thread_id):
                return True

            state = self._runner.get_state(thread_id)
            has_checkpoint = bool(state.values)
            has_metadata = self._metadata_for(thread_id) is not None
            if not has_checkpoint and not has_metadata:
                return False

            self._delete_thread_storage(thread_id)
            return True

    @property
    def agent(self):
        """Expose the compiled graph for compatibility and diagnostics."""

        return self._runner.agent

    def close(self) -> None:
        """Close resources owned by this runtime."""

        with self._lock:
            self._observability.close()
            if self._persistence is not None:
                self._persistence.close()
                self._persistence = None
                self._conversation_service = None

    def _create_context(
        self,
        *,
        thread_id: str,
        workspace_id: str,
        project_id: str | None,
        user_id: str | None,
        run_id: str | None,
    ) -> ExecutionContext:
        return ExecutionContext(
            thread_id=thread_id,
            workspace_id=workspace_id,
            project_id=project_id,
            user_id=user_id,
            **({"run_id": run_id} if run_id is not None else {}),
        )

    def _run_graph(
        self,
        context: ExecutionContext,
        control: RunControl,
        message: str,
    ) -> dict[str, Any]:
        if control.drain_requested:
            raise AgentCancelledError(control.drain_reason or "client_cancelled")

        state = self._runner.invoke(
            message=message,
            context=context,
            control=control,
        )
        if control.drain_requested:
            raise AgentCancelledError(control.drain_reason or "client_cancelled")
        return state

    def _turn_from_state(
        self,
        thread_id: str,
        state: dict[str, Any],
    ) -> AgentTurn:
        direct_response = state.get("response")
        if isinstance(direct_response, str) and direct_response.strip():
            result = state.get("result")
            archhypo = archhypo_from_value(result) if result is not None else None
            response = AIMessage(content=direct_response)
        else:
            archhypo = archhypo_from_value(state.get("result"))
            response = response_message(archhypo)
        self._ensure_conversation(thread_id)
        return AgentTurn(thread_id=thread_id, message=response, result=archhypo)

    def _register_run(
        self,
        context: ExecutionContext,
        control: RunControl,
        message: str,
    ) -> None:
        with self._lock:
            self._runs.register(context, control)
            try:
                self._ensure_conversation(context.thread_id, message)
            except Exception:
                self._runs.unregister(context.run_id)
                raise

    def _finish_run(self, run_id: str) -> None:
        with self._lock:
            thread_id = self._runs.finish(run_id)
            if thread_id is not None:
                self._delete_thread_storage(thread_id)

    def _ensure_conversation(self, thread_id: str, title: str | None = None) -> None:
        if self._conversation_service is not None:
            self._conversation_service.ensure(thread_id, title)

    def _metadata_for(self, thread_id: str):
        if self._conversation_service is None:
            return None
        return self._conversation_service.get(thread_id)

    def _conversation_metadata(self):
        if self._conversation_service is None:
            return {}
        return {item.thread_id: item for item in self._conversation_service.list()}

    def _delete_thread_storage(self, thread_id: str) -> None:
        if self._persistence is not None:
            self._persistence.delete_thread(thread_id)
        else:
            self._runner.delete_thread(thread_id)


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
            message_text(message)
            for message in messages
            if message_role(message) == "user" and message_text(message)
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
        role = message_role(message)
        text = message_text(message)
        if role in ("user", "assistant") and text:
            result.append(ConversationMessage(role=role, content=text))
    return result


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
