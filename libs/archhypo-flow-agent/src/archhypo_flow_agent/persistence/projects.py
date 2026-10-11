"""Project metadata contracts and SQLite repository."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ProjectMetadata:
    id: str
    name: str
    icon: str
    color: str
    instructions: str
    created_at: str
    updated_at: str


class ProjectRepository(Protocol):
    def list(self) -> list[ProjectMetadata]: ...

    def get(self, project_id: str) -> ProjectMetadata | None: ...

    def create(
        self,
        *,
        project_id: str,
        name: str,
        icon: str,
        color: str,
        instructions: str,
    ) -> ProjectMetadata: ...

    def rename(self, project_id: str, name: str) -> ProjectMetadata | None: ...

    def update(
        self,
        project_id: str,
        *,
        name: str,
        icon: str,
        color: str,
        instructions: str,
    ) -> ProjectMetadata | None: ...


class SQLiteProjectRepository:
    """Persist projects in the shared local SQLite database."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def list(self) -> list[ProjectMetadata]:
        rows = self._connection.execute(
            """
            SELECT id, name, icon, color, instructions, created_at, updated_at
            FROM projects
            ORDER BY created_at DESC, id
            """
        ).fetchall()
        return [_project_from_row(row) for row in rows]

    def get(self, project_id: str) -> ProjectMetadata | None:
        row = self._connection.execute(
            """
            SELECT id, name, icon, color, instructions, created_at, updated_at
            FROM projects
            WHERE id = ?
            """,
            (project_id,),
        ).fetchone()
        return _project_from_row(row) if row else None

    def create(
        self,
        *,
        project_id: str,
        name: str,
        icon: str,
        color: str,
        instructions: str,
    ) -> ProjectMetadata:
        now = _now()
        self._connection.execute(
            """
            INSERT OR IGNORE INTO projects
                (id, name, icon, color, instructions, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (project_id, _clean_name(name), icon, color, instructions, now, now),
        )
        self._connection.commit()
        project = self.get(project_id)
        if project is None:
            raise RuntimeError("Project was not persisted")
        return project

    def rename(self, project_id: str, name: str) -> ProjectMetadata | None:
        self._connection.execute(
            "UPDATE projects SET name = ?, updated_at = ? WHERE id = ?",
            (_clean_name(name), _now(), project_id),
        )
        self._connection.commit()
        return self.get(project_id)

    def update(
        self,
        project_id: str,
        *,
        name: str,
        icon: str,
        color: str,
        instructions: str,
    ) -> ProjectMetadata | None:
        self._connection.execute(
            """
            UPDATE projects
            SET name = ?, icon = ?, color = ?, instructions = ?, updated_at = ?
            WHERE id = ?
            """,
            (_clean_name(name), icon, color, instructions, _now(), project_id),
        )
        self._connection.commit()
        return self.get(project_id)


def _project_from_row(row: sqlite3.Row | tuple[object, ...]) -> ProjectMetadata:
    return ProjectMetadata(
        id=str(row[0]),
        name=str(row[1]),
        icon=str(row[2]),
        color=str(row[3]),
        instructions=str(row[4]),
        created_at=str(row[5]),
        updated_at=str(row[6]),
    )


def _clean_name(value: str) -> str:
    return " ".join(value.split())[:80].rstrip()


def _now() -> str:
    return datetime.now(UTC).isoformat()


__all__ = ["ProjectMetadata", "ProjectRepository", "SQLiteProjectRepository"]
