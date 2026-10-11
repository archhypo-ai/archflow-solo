"""Application-facing chat, conversation, and SQLite operations."""

from __future__ import annotations

from pathlib import Path
from threading import RLock
from typing import cast

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.checkpoint.base import BaseCheckpointSaver

from archhypo_flow_agent.core import ChatRequest, ChatResponse
from archhypo_flow_agent.graph import build_graph
from archhypo_flow_agent.persistence.conversations import ConversationMetadata
from archhypo_flow_agent.persistence.paths import DATABASE_PATH
from archhypo_flow_agent.persistence.projects import ProjectMetadata
from archhypo_flow_agent.persistence.sqlite import (
    SQLitePersistence,
    open_sqlite_persistence,
)

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
    ) -> None:
        self._lock = RLock()
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

        try:
            self._graph = build_graph(active_model, checkpointer=active_checkpointer)
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

            result = self._graph.invoke(
                {"messages": [HumanMessage(content=request.message)]},
                config={"configurable": {"thread_id": request.thread_id}},
            )
            messages = result.get("messages", [])
            if not messages:
                raise RuntimeError("The chat graph returned no messages")

            last_message = cast(BaseMessage, messages[-1])
            if metadata is None:
                title = _title_from_message(request.message)
            else:
                title = metadata.title

            return ChatResponse(
                thread_id=request.thread_id,
                title=title,
                message=_message_text(last_message),
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
        for raw_message in raw_messages:
            message = cast(BaseMessage, raw_message)
            if message.type == "human":
                projected.append(
                    ConversationMessage(role="user", content=_message_text(message))
                )
            elif message.type == "ai" and _message_text(message):
                projected.append(
                    ConversationMessage(
                        role="assistant",
                        content=_message_text(message),
                    )
                )
        return projected


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
