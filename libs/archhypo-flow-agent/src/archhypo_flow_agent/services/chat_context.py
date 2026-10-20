"""Resolve project data for one chat execution."""

from archhypo_flow_agent.config import settings
from archhypo_flow_agent.core import AgentRunContext, ChatRequest
from archhypo_flow_agent.persistence.conversations import (
    ConversationMetadata,
    ConversationRepository,
)
from archhypo_flow_agent.persistence.projects import ProjectRepository


class ChatContextResolver:
    """Resolve and persist a conversation's project association for a turn."""

    def __init__(
        self,
        conversations: ConversationRepository | None,
        projects: ProjectRepository | None,
    ) -> None:
        self._conversations = conversations
        self._projects = projects

    def resolve(
        self,
        request: ChatRequest,
    ) -> tuple[ConversationMetadata | None, AgentRunContext]:
        metadata = None
        if self._conversations is not None:
            existing = self._conversations.get(request.thread_id)
            if request.project_id is not None and (
                existing is None or existing.project_id is None
            ):
                self._require_project(request.project_id)

            metadata = self._conversations.ensure(
                request.thread_id,
                request.message,
            )
            if metadata.project_id is None and request.project_id is not None:
                metadata = self._conversations.set_project(
                    request.thread_id,
                    request.project_id,
                )
        elif request.project_id is not None:
            raise LookupError("Project persistence is not available.")

        project_context = ""
        project_id = metadata.project_id if metadata is not None else None
        if project_id is not None and self._projects is not None:
            project = self._projects.get(project_id)
            if project is not None:
                project_context = project.instructions

        return metadata, {
            "global_context": request.global_context,
            "project_context": project_context,
            "language": request.language,
            "hitl_enabled": settings.hitl_enabled and request.hitl_enabled,
        }

    def _require_project(self, project_id: str) -> None:
        if self._projects is None or self._projects.get(project_id) is None:
            raise LookupError("Project not found.")


__all__ = ["ChatContextResolver"]
