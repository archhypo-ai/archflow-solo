"""Application facade for chat, conversations, projects, and persistence."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from threading import Lock
from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver

from archhypo_flow_agent.config import AgentSettings, settings
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
from archhypo_flow_agent.providers import (
    SystemOneClient,
    create_openrouter_model,
    create_system_one_client,
)
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
        chat_model_id: str | None = None,
        system_one_model_id: str | None = None,
        configuration: AgentSettings | None = None,
        provider_settings_resolver: Callable[[], AgentSettings] | None = None,
    ) -> None:
        if model is not None and system_one_client is None:
            raise ValueError("A SystemOne client is required for request routing.")
        self._lock = Lock()
        self._runtime_lock = Lock()
        self._provider_settings_resolver = provider_settings_resolver
        self._runtime_signature: tuple | None = None
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
        artifacts = artifact_repository or (
            self._persistence.artifacts if self._persistence is not None else None
        )
        self._artifact_repository = artifacts
        active_tools = [tavily_search] if tools is None else _resolve_tools(tools)
        self._active_checkpointer = active_checkpointer
        self._active_tools = active_tools
        self._dynamic_tavily = tools is None
        if (
            model is not None
            and configuration is not None
            and provider_settings_resolver
        ):
            self._runtime_signature = _provider_signature(configuration)

        try:
            if model is not None and artifacts is None:
                raise ValueError(
                    "An artifact repository is required for ArchHypo chat."
                )
            graph = (
                build_graph(
                    model,
                    tools=active_tools,
                    dynamic_tavily=tools is None,
                    checkpointer=active_checkpointer,
                    system_one_client=system_one_client,
                    artifact_repository=artifacts,
                    chat_model_id=chat_model_id or settings.openrouter_model,
                    system_one_model_id=system_one_model_id
                    or settings.system_one_model,
                )
                if model is not None
                else build_history_graph(active_checkpointer)
            )
        except Exception:
            self.close()
            raise

        self._chat: ChatExecutionService | None = None
        if model is not None:
            self._observability = build_observability(configuration or settings)
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
        with self._runtime_lock:
            with self._lock:
                self._refresh_runtime()
            if self._chat is None:
                raise ChatNotConfiguredError("A chat model is not configured.")
            return self._chat.respond(request)

    def stream(
        self,
        request: ChatRequest,
        *,
        run_id: str | None = None,
    ) -> Iterator[dict[str, object]]:
        # Hold the same lock for the entire stream so a later request cannot
        # replace clients while this turn is still running.
        with self._runtime_lock:
            with self._lock:
                self._refresh_runtime()
            if self._chat is None:
                raise ChatNotConfiguredError("A chat model is not configured.")
            yield from self._chat.stream(request, run_id=run_id)

    @property
    def dynamic_provider_settings(self) -> bool:
        return self._provider_settings_resolver is not None

    def runtime_configuration_error(self) -> str | None:
        if self._provider_settings_resolver is None:
            return None if self.chat_ready else "A chat model is not configured."
        try:
            configuration = self._provider_settings_resolver()
            configuration.require_openrouter_api_key()
            configuration.require_system_one_model()
        except (OSError, ValueError) as error:
            return str(error)
        return None

    def _refresh_runtime(self) -> None:
        if self._provider_settings_resolver is None:
            return
        try:
            configuration = self._provider_settings_resolver()
            signature = _provider_signature(configuration)
            if signature == self._runtime_signature:
                return
            system_one = create_system_one_client(configuration)
            model = create_openrouter_model(configuration)
            if self._artifact_repository is None:
                raise ValueError(
                    "An artifact repository is required for ArchHypo chat."
                )
            graph = build_graph(
                model,
                tools=self._active_tools,
                dynamic_tavily=self._dynamic_tavily,
                checkpointer=self._active_checkpointer,
                system_one_client=system_one,
                artifact_repository=self._artifact_repository,
                chat_model_id=configuration.openrouter_model,
                system_one_model_id=configuration.system_one_model,
            )
        except (OSError, ValueError) as error:
            raise ChatNotConfiguredError(str(error)) from error
        if self._observability is None:
            self._observability = build_observability(configuration)
        if self._chat is None:
            conversations = (
                self._persistence.conversations if self._persistence else None
            )
            projects = self._persistence.projects if self._persistence else None
            self._chat = ChatExecutionService(
                graph,
                ChatContextResolver(conversations, projects),
                self._lock,
                self._observability,
            )
        else:
            self._chat.replace_graph(graph)
        self._conversations.replace_graph(graph)
        self._runtime_signature = signature

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

    def get_artifact(self, artifact_id: str) -> ArchHypoArtifactRecord | None:
        if self._artifact_repository is None:
            return None
        with self._lock:
            return self._artifact_repository.get_by_id(artifact_id)

    def update_artifact_status(
        self,
        artifact_id: str,
        status: Literal["open", "closed"],
    ) -> ArchHypoArtifactRecord | None:
        if self._artifact_repository is None:
            return None
        with self._lock:
            return self._artifact_repository.update_status(artifact_id, status)

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
        with self._runtime_lock, self._lock:
            if self._observability is not None:
                self._observability.close()
                self._observability = None
            if self._persistence is not None:
                self._persistence.close()
                self._persistence = None


def _provider_signature(configuration: AgentSettings) -> tuple:
    key = configuration.require_openrouter_api_key()
    system_model = configuration.require_system_one_model()
    return (
        hashlib.sha256(key.encode("utf-8")).digest(),
        configuration.openrouter_model,
        system_model,
        configuration.system_one_endpoint,
        configuration.system_one_timeout,
    )


def _resolve_tools(tools: Sequence[BaseTool] | None) -> list[BaseTool]:
    if tools is not None:
        return list(tools)
    if settings.tavily_api_key and settings.tavily_api_key.get_secret_value().strip():
        return [tavily_search]
    return []


__all__ = ["AgentService", "ChatNotConfiguredError"]
