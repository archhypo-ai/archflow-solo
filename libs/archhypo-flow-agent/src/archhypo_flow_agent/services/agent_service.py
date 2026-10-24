"""Application facade for chat, conversations, projects, and persistence."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from pathlib import Path
from threading import Lock

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver

from archhypo_flow_agent.config import settings
from archhypo_flow_agent.core import ChatRequest, ChatResponse
from archhypo_flow_agent.graph import build_graph, build_history_graph
from archhypo_flow_agent.observability import Observability, build_observability
from archhypo_flow_agent.persistence.artifacts import (
    ArchHypoArtifactRecord,
    ArchHypoArtifactRepository,
)
from archhypo_flow_agent.persistence.paths import DATABASE_PATH
from archhypo_flow_agent.persistence.projects import ProjectMetadata
from archhypo_flow_agent.persistence.sqlite import (
    SQLitePersistence,
    open_sqlite_persistence,
)
from archhypo_flow_agent.providers import SystemOneClient
from archhypo_flow_agent.tools import tavily_search

from .chat_context import ChatContextResolver
from .chat_execution import ChatExecutionService
from .contracts import Conversation, ConversationSummary
from .conversation_service import ConversationService
from .project_service import ProjectService


class ChatNotConfiguredError(RuntimeError):
    """Raised when a chat operation is attempted without a configured model."""


class AgentService:
    """Wire application services and expose their stable API to FastAPI."""

    def __init__(
        self,
        *,
        model: BaseChatModel | None = None,
        checkpointer: BaseCheckpointSaver | None = None,
        database_path: Path | None = None,
        tools: Sequence[BaseTool] | None = None,
        system_one_client: SystemOneClient | None = None,
        artifact_repository: ArchHypoArtifactRepository | None = None,
    ) -> None:
        if model is not None and system_one_client is None:
            raise ValueError("A SystemOne client is required for request routing.")
        self._lock = Lock()
        self._persistence: SQLitePersistence | None = None
        self._observability: Observability | None = None
        self._artifact_repository: ArchHypoArtifactRepository | None = None
        if checkpointer is None:
            self._persistence = open_sqlite_persistence(database_path or DATABASE_PATH)
            active_checkpointer = self._persistence.checkpointer
        else:
            active_checkpointer = checkpointer

        conversations = self._persistence.conversations if self._persistence else None
        projects = self._persistence.projects if self._persistence else None
        artifacts = (
            artifact_repository
            or (self._persistence.artifacts if self._persistence is not None else None)
        )
        self._artifact_repository = artifacts
        active_tools = _resolve_tools(tools)

        try:
            if model is not None and artifacts is None:
                raise ValueError(
                    "An artifact repository is required for ArchHypo chat."
                )
            graph = (
                build_graph(
                    model,
                    tools=active_tools,
                    checkpointer=active_checkpointer,
                    system_one_client=system_one_client,
                    artifact_repository=artifacts,
                    chat_model_id=settings.openrouter_model,
                    system_one_model_id=settings.system_one_model,
                )
                if model is not None
                else build_history_graph(active_checkpointer)
            )
        except Exception:
            self.close()
            raise

        self._chat: ChatExecutionService | None = None
        if model is not None:
            self._observability = build_observability(settings)
            assert self._observability is not None
            self._chat = ChatExecutionService(
                graph,
                ChatContextResolver(conversations, projects),
                self._lock,
                self._observability,
            )

        self._conversations = ConversationService(
            graph=graph,
            conversations=conversations,
            projects=projects,
            persistence=self._persistence,
            lock=self._lock,
        )
        self._projects = ProjectService(self._persistence, self._lock)

    @property
    def chat_ready(self) -> bool:
        return self._chat is not None

    def respond(self, request: ChatRequest) -> ChatResponse:
        if self._chat is None:
            raise ChatNotConfiguredError("A chat model is not configured.")
        return self._chat.respond(request)

    def stream(
        self,
        request: ChatRequest,
        *,
        run_id: str | None = None,
    ) -> Iterator[dict[str, object]]:
        if self._chat is None:
            raise ChatNotConfiguredError("A chat model is not configured.")
        return self._chat.stream(request, run_id=run_id)

    def list_conversations(self) -> list[ConversationSummary]:
        return self._conversations.list()

    def get_conversation(self, thread_id: str) -> Conversation | None:
        return self._conversations.get(thread_id)

    def update_conversation(
        self,
        thread_id: str,
        *,
        title: str | None = None,
        pinned: bool | None = None,
    ) -> ConversationSummary | None:
        return self._conversations.update(thread_id, title=title, pinned=pinned)

    def set_conversation_project(
        self,
        thread_id: str,
        project_id: str | None,
    ) -> ConversationSummary | None:
        return self._conversations.set_project(thread_id, project_id)

    def delete_conversation(self, thread_id: str) -> bool:
        return self._conversations.delete(thread_id)

    def list_projects(self) -> list[ProjectMetadata]:
        return self._projects.list()

    def list_artifacts(
        self,
        *,
        project_id: str | None = None,
    ) -> list[ArchHypoArtifactRecord]:
        if self._artifact_repository is None:
            return []
        with self._lock:
            return self._artifact_repository.list(project_id=project_id)

    def get_project(self, project_id: str) -> ProjectMetadata | None:
        return self._projects.get(project_id)

    def create_project(
        self,
        *,
        project_id: str,
        name: str,
        icon: str,
        color: str,
        instructions: str = "",
    ) -> ProjectMetadata:
        return self._projects.create(
            project_id=project_id,
            name=name,
            icon=icon,
            color=color,
            instructions=instructions,
        )

    def rename_project(self, project_id: str, name: str) -> ProjectMetadata | None:
        return self._projects.rename(project_id, name)

    def update_project_settings(
        self,
        project_id: str,
        *,
        name: str,
        icon: str,
        color: str,
        instructions: str,
    ) -> ProjectMetadata | None:
        return self._projects.update_settings(
            project_id,
            name=name,
            icon=icon,
            color=color,
            instructions=instructions,
        )

    def delete_project(self, project_id: str) -> bool:
        return self._projects.delete(project_id)

    def close(self) -> None:
        with self._lock:
            if self._observability is not None:
                self._observability.close()
                self._observability = None
            if self._persistence is not None:
                self._persistence.close()
                self._persistence = None


def _resolve_tools(tools: Sequence[BaseTool] | None) -> list[BaseTool]:
    if tools is not None:
        return list(tools)
    if settings.tavily_api_key and settings.tavily_api_key.get_secret_value().strip():
        return [tavily_search]
    return []


__all__ = ["AgentService", "ChatNotConfiguredError"]
