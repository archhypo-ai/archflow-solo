"""Project metadata operations."""

from threading import Lock

from archhypo_flow_agent.persistence.projects import ProjectMetadata
from archhypo_flow_agent.persistence.sqlite import SQLitePersistence


class ProjectService:
    """Manage project records and their cascading deletion."""

    def __init__(self, persistence: SQLitePersistence | None, lock: Lock) -> None:
        self._persistence = persistence
        self._lock = lock

    def list(self) -> list[ProjectMetadata]:
        if self._persistence is None:
            return []
        with self._lock:
            return self._persistence.projects.list()

    def get(self, project_id: str) -> ProjectMetadata | None:
        if self._persistence is None or not project_id.strip():
            return None
        with self._lock:
            return self._persistence.projects.get(project_id)

    def create(
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

    def rename(self, project_id: str, name: str) -> ProjectMetadata | None:
        if self._persistence is None or not project_id.strip():
            return None
        with self._lock:
            return self._persistence.projects.rename(project_id, name)

    def update_settings(
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

    def delete(self, project_id: str) -> bool:
        if self._persistence is None or not project_id.strip():
            return False
        with self._lock:
            return self._persistence.delete_project(project_id)


__all__ = ["ProjectService"]
