"""Application-facing chat, conversation, and SQLite operations."""

from __future__ import annotations

import json
from collections.abc import Iterator, Sequence
from pathlib import Path
from threading import Lock
from typing import cast
from uuid import uuid4

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver

from archhypo_flow_agent.config import settings
from archhypo_flow_agent.core import ChatRequest, ChatResponse, ToolCallRecord
from archhypo_flow_agent.graph import build_graph
from archhypo_flow_agent.persistence.conversations import ConversationMetadata
from archhypo_flow_agent.persistence.paths import DATABASE_PATH
from archhypo_flow_agent.persistence.projects import ProjectMetadata
from archhypo_flow_agent.persistence.sqlite import (
    SQLitePersistence,
    open_sqlite_persistence,
)
from archhypo_flow_agent.tools import tavily_search

from .contracts import Conversation, ConversationMessage, ConversationSummary
from .demo_model import DemoChatModel


class AgentService:
    """Run one local chat graph and expose its saved conversations."""

    def __init__(
        self,
        *,
        model: BaseChatModel | None = None,
        checkpointer: BaseCheckpointSaver | None = None,
        database_path: Path | None = None,
        tools: Sequence[BaseTool] | None = None,
    ) -> None:
        # The SSE iterator may resume on different worker threads between yields.
        self._lock = Lock()
        self._demo_model = DemoChatModel() if model is None else None
        active_model = model or self._demo_model
        if active_model is None:
            raise RuntimeError("A chat model is required")

        self._persistence: SQLitePersistence | None = None
        if checkpointer is None:
            self._persistence = open_sqlite_persistence(database_path or DATABASE_PATH)
            active_checkpointer = self._persistence.checkpointer
            self._conversations = self._persistence.conversations
        else:
            active_checkpointer = checkpointer
            self._conversations = None

        active_tools = (
            list(tools)
            if tools is not None
            else (
                [tavily_search]
                if settings.tavily_api_key
                and settings.tavily_api_key.get_secret_value().strip()
                else []
            )
        )
        try:
            self._graph = build_graph(
                active_model,
                tools=active_tools,
                checkpointer=active_checkpointer,
            )
        except Exception:
            self.close()
            raise

    def respond(self, request: ChatRequest) -> ChatResponse:
        """Persist one user turn and return the assistant's visible reply."""

        with self._lock:
            if self._demo_model is not None:
                self._demo_model.set_language(request.language)

            metadata = None
            if self._conversations is not None:
                metadata = self._conversations.ensure(
                    request.thread_id,
                    request.message,
                )
                if request.project_id is not None:
                    if self._persistence is None:
                        raise LookupError("Project not found.")
                    if self._persistence.projects.get(request.project_id) is None:
                        raise LookupError("Project not found.")
                    metadata = self._conversations.set_project(
                        request.thread_id,
                        request.project_id,
                    )
            elif request.project_id is not None:
                raise LookupError("Project persistence is not available.")

            config = {"configurable": {"thread_id": request.thread_id}}
            previous_state = self._graph.get_state(config)
            previous_values = (
                previous_state.values if isinstance(previous_state.values, dict) else {}
            )
            previous_messages = previous_values.get("messages", [])
            previous_message_count = len(previous_messages)

            result = self._graph.invoke(
                {"messages": [HumanMessage(content=request.message)]},
                config=config,
            )
            messages = result.get("messages", [])
            if not messages:
                raise RuntimeError("The chat graph returned no messages")

            turn_messages = messages[previous_message_count:]
            last_message = cast(BaseMessage, messages[-1])
            if metadata is None:
                title = _title_from_message(request.message)
            else:
                title = metadata.title

            return ChatResponse(
                thread_id=request.thread_id,
                title=title,
                message=_message_text(last_message),
                tool_calls=_tool_calls_from_messages(turn_messages),
            )

    def stream(
        self,
        request: ChatRequest,
        *,
        run_id: str | None = None,
    ) -> Iterator[dict[str, object]]:
        """Stream tool progress and the final assistant reply for one turn."""

        active_run_id = run_id or uuid4().hex
        yield _stream_event_data(
            active_run_id,
            request.thread_id,
            "phase",
            phase="thinking",
        )
        with self._lock:
            if self._demo_model is not None:
                self._demo_model.set_language(request.language)

            metadata = None
            if self._conversations is not None:
                metadata = self._conversations.ensure(
                    request.thread_id,
                    request.message,
                )
                if request.project_id is not None:
                    if self._persistence is None:
                        raise LookupError("Project not found.")
                    if self._persistence.projects.get(request.project_id) is None:
                        raise LookupError("Project not found.")
                    metadata = self._conversations.set_project(
                        request.thread_id,
                        request.project_id,
                    )
            elif request.project_id is not None:
                raise LookupError("Project persistence is not available.")

            config = {"configurable": {"thread_id": request.thread_id}}
            previous_state = self._graph.get_state(config)
            previous_values = (
                previous_state.values if isinstance(previous_state.values, dict) else {}
            )
            previous_messages = previous_values.get("messages", [])
            previous_tool_ids = {
                call.id
                for call in _tool_calls_from_messages(
                    cast(Sequence[BaseMessage], previous_messages)
                )
            }
            emitted_calls = set(previous_tool_ids)
            emitted_results = set(previous_tool_ids)
            pending_calls: set[str] = set()

            for _, mode, update in self._graph.stream(
                {"messages": [HumanMessage(content=request.message)]},
                config=config,
                stream_mode=["updates"],
                subgraphs=True,
            ):
                if mode != "updates":
                    continue
                for message in _messages_from_update(update):
                    if message.type == "ai":
                        for index, call in enumerate(
                            getattr(message, "tool_calls", [])
                        ):
                            call_id = str(call.get("id") or f"tool-call-{index}")
                            if call_id in emitted_calls:
                                continue
                            emitted_calls.add(call_id)
                            pending_calls.add(call_id)
                            args = call.get("args")
                            normalized_args = args if isinstance(args, dict) else {}
                            yield _stream_event_data(
                                active_run_id,
                                request.thread_id,
                                "tool_call_start",
                                tool_call_id=call_id,
                                name=str(call.get("name") or "unknown_tool"),
                            )
                            yield _stream_event_data(
                                active_run_id,
                                request.thread_id,
                                "tool_call_delta",
                                tool_call_id=call_id,
                                text=json.dumps(
                                    normalized_args,
                                    ensure_ascii=False,
                                    default=str,
                                ),
                            )
                    elif message.type == "tool":
                        call_id = str(getattr(message, "tool_call_id", ""))
                        if not call_id or call_id in emitted_results:
                            continue
                        emitted_results.add(call_id)
                        pending_calls.discard(call_id)
                        yield _stream_event_data(
                            active_run_id,
                            request.thread_id,
                            "tool_result",
                            tool_call_id=call_id,
                            output=_tool_result_value(message.content),
                            is_error=(
                                getattr(message, "status", "success") == "error"
                            ),
                        )
                        if not pending_calls:
                            yield _stream_event_data(
                                active_run_id,
                                request.thread_id,
                                "phase",
                                phase="thinking",
                            )

            final_state = self._graph.get_state(config)
            final_values = (
                final_state.values if isinstance(final_state.values, dict) else {}
            )
            messages = final_values.get("messages", [])
            if not messages:
                raise RuntimeError("The chat graph returned no messages")

            last_message = cast(BaseMessage, messages[-1])
            message_text = _message_text(last_message)
            if not message_text:
                raise RuntimeError("The chat graph returned an empty reply")
            title = metadata.title if metadata is not None else _title_from_message(
                request.message
            )

            yield _stream_event_data(
                active_run_id,
                request.thread_id,
                "phase",
                phase="answering",
            )
            yield _stream_event_data(
                active_run_id,
                request.thread_id,
                "text_delta",
                text=message_text,
            )
            yield _stream_event_data(
                active_run_id,
                request.thread_id,
                "done",
                status="completed",
                title=title,
                message=message_text,
            )

    def list_conversations(self) -> list[ConversationSummary]:
        """List saved threads newest-first with visible message counts."""

        if self._conversations is None:
            return []
        with self._lock:
            summaries = []
            for metadata in self._conversations.list():
                messages = self._load_messages(metadata.thread_id)
                summaries.append(self._conversation_summary(metadata, messages))
            return summaries

    def get_conversation(self, thread_id: str) -> Conversation | None:
        """Load a saved thread transcript from its LangGraph checkpoint."""

        if not thread_id.strip() or self._conversations is None:
            return None
        with self._lock:
            metadata = self._conversations.get(thread_id)
            if metadata is None:
                return None
            messages = self._load_messages(thread_id)
            return Conversation(
                thread_id=thread_id,
                title=metadata.title,
                message_count=len(messages),
                updated_at=metadata.updated_at,
                pinned=metadata.pinned,
                project_id=metadata.project_id,
                preview=messages[-1].content if messages else "",
                messages=messages,
            )

    def update_conversation(
        self,
        thread_id: str,
        *,
        title: str | None = None,
        pinned: bool | None = None,
    ) -> ConversationSummary | None:
        """Update the title or pinned state of a saved conversation."""

        if not thread_id.strip() or self._conversations is None:
            return None
        with self._lock:
            metadata = self._conversations.update(
                thread_id,
                title=title,
                pinned=pinned,
            )
            if metadata is None:
                return None
            return self._conversation_summary(metadata)

    def set_conversation_project(
        self,
        thread_id: str,
        project_id: str | None,
    ) -> ConversationSummary | None:
        """Associate a conversation with a project, or clear that association."""

        if not thread_id.strip() or self._conversations is None:
            return None
        with self._lock:
            if project_id is not None:
                if self._persistence is None:
                    raise LookupError("Project not found.")
                if self._persistence.projects.get(project_id) is None:
                    raise LookupError("Project not found.")
            metadata = self._conversations.set_project(thread_id, project_id)
            if metadata is None:
                return None
            return self._conversation_summary(metadata)

    def list_projects(self) -> list[ProjectMetadata]:
        if self._persistence is None:
            return []
        with self._lock:
            return self._persistence.projects.list()

    def get_project(self, project_id: str) -> ProjectMetadata | None:
        if self._persistence is None or not project_id.strip():
            return None
        with self._lock:
            return self._persistence.projects.get(project_id)

    def create_project(
        self,
        *,
        project_id: str,
        name: str,
        icon: str,
        color: str,
        instructions: str = "",
    ) -> ProjectMetadata:
        if self._persistence is None:
            raise RuntimeError("Project persistence is not available")
        with self._lock:
            return self._persistence.projects.create(
                project_id=project_id,
                name=name,
                icon=icon,
                color=color,
                instructions=instructions,
            )

    def rename_project(self, project_id: str, name: str) -> ProjectMetadata | None:
        if self._persistence is None or not project_id.strip():
            return None
        with self._lock:
            return self._persistence.projects.rename(project_id, name)

    def update_project_settings(
        self,
        project_id: str,
        *,
        name: str,
        icon: str,
        color: str,
        instructions: str,
    ) -> ProjectMetadata | None:
        if self._persistence is None or not project_id.strip():
            return None
        with self._lock:
            return self._persistence.projects.update(
                project_id,
                name=name,
                icon=icon,
                color=color,
                instructions=instructions,
            )

    def delete_project(self, project_id: str) -> bool:
        if self._persistence is None or not project_id.strip():
            return False
        with self._lock:
            return self._persistence.delete_project(project_id)

    def delete_conversation(self, thread_id: str) -> bool:
        """Remove the saved checkpoint and conversation metadata."""

        if not thread_id.strip() or self._persistence is None:
            return False
        with self._lock:
            return self._persistence.delete_thread(thread_id)

    def close(self) -> None:
        """Close SQLite resources owned by this service."""

        with self._lock:
            if self._persistence is not None:
                self._persistence.close()
                self._persistence = None

    def _conversation_summary(
        self,
        metadata: ConversationMetadata,
        messages: list[ConversationMessage] | None = None,
    ) -> ConversationSummary:
        visible_messages = (
            messages
            if messages is not None
            else self._load_messages(metadata.thread_id)
        )
        return ConversationSummary(
            thread_id=metadata.thread_id,
            title=metadata.title,
            message_count=len(visible_messages),
            updated_at=metadata.updated_at,
            pinned=metadata.pinned,
            project_id=metadata.project_id,
            preview=visible_messages[-1].content if visible_messages else "",
        )

    def _load_messages(self, thread_id: str) -> list[ConversationMessage]:
        state = self._graph.get_state(
            {"configurable": {"thread_id": thread_id}}
        )
        values = state.values if isinstance(state.values, dict) else {}
        raw_messages = values.get("messages", [])
        projected: list[ConversationMessage] = []
        turn_messages: list[BaseMessage] = []
        for raw_message in raw_messages:
            message = cast(BaseMessage, raw_message)
            if message.type == "human":
                turn_messages = []
                projected.append(
                    ConversationMessage(role="user", content=_message_text(message))
                )
                continue

            if message.type not in {"ai", "tool"}:
                continue
            turn_messages.append(message)
            text = _message_text(message)
            has_tool_calls = bool(getattr(message, "tool_calls", []))
            if message.type == "ai" and text and not has_tool_calls:
                projected.append(
                    ConversationMessage(
                        role="assistant",
                        content=text,
                        tool_calls=_tool_calls_from_messages(turn_messages),
                    )
                )
                turn_messages = []
        return projected


def _stream_event_data(
    run_id: str,
    thread_id: str,
    event_type: str,
    **fields: object,
) -> dict[str, object]:
    return {
        "protocol_version": 1,
        "run_id": run_id,
        "thread_id": thread_id,
        "type": event_type,
        **fields,
    }


def _messages_from_update(update: object) -> Iterator[BaseMessage]:
    if not isinstance(update, dict):
        return

    values = list(update.values())
    while values:
        value = values.pop()
        if not isinstance(value, dict):
            continue
        messages = value.get("messages")
        if isinstance(messages, list):
            yield from (
                message for message in messages if isinstance(message, BaseMessage)
            )
        values.extend(child for child in value.values() if isinstance(child, dict))


def _tool_calls_from_messages(
    messages: Sequence[BaseMessage],
) -> list[ToolCallRecord]:
    calls: list[dict[str, object]] = []
    calls_by_id: dict[str, dict[str, object]] = {}

    for message in messages:
        if message.type == "ai":
            for index, call in enumerate(getattr(message, "tool_calls", [])):
                call_id = str(call.get("id") or f"tool-call-{index}")
                args = call.get("args")
                record: dict[str, object] = {
                    "id": call_id,
                    "name": str(call.get("name") or "unknown_tool"),
                    "args": args if isinstance(args, dict) else {},
                    "result": None,
                    "is_error": False,
                }
                calls.append(record)
                calls_by_id[call_id] = record
        elif message.type == "tool":
            call_id = str(getattr(message, "tool_call_id", ""))
            record = calls_by_id.get(call_id)
            if record is not None:
                record["result"] = _tool_result_value(message.content)
                record["is_error"] = getattr(message, "status", "success") == "error"

    return [ToolCallRecord(**call) for call in calls]


def _tool_result_value(content: object) -> object:
    if not isinstance(content, str):
        return content
    try:
        decoded = json.loads(content)
    except ValueError:
        return content
    return decoded if isinstance(decoded, (dict, list)) else content


def _message_text(message: BaseMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    return "".join(
        str(block["text"])
        for block in content
        if isinstance(block, dict) and isinstance(block.get("text"), str)
    )


def _title_from_message(message: str) -> str:
    return " ".join(message.split())[:80].rstrip() or "Untitled conversation"


__all__ = ["AgentService"]
