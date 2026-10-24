"""SQLite persistence for final ArchHypo result snapshots."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal, Protocol
from uuid import uuid4

from archhypo_flow_agent.core import ArchHypoResult, RequestRouting


class ArtifactPersistenceError(RuntimeError):
    """A final ArchHypo result could not be stored consistently."""


@dataclass(frozen=True, slots=True)
class ArchHypoArtifactRecord:
    id: str
    cycle_id: str
    thread_id: str
    project_id: str | None
    title: str
    status: str
    outcome: str
    hitl_enabled: bool
    chat_model: str | None
    system_one_model: str | None
    result_schema_version: int
    routing: dict[str, object]
    review_history: list[dict[str, object]]
    result: dict[str, object]
    created_at: str
    updated_at: str


class ArchHypoArtifactRepository(Protocol):
    """Persist one immutable ArchHypo snapshot per workflow cycle."""

    def save_final_result(
        self,
        *,
        cycle_id: str,
        thread_id: str,
        project_id: str | None,
        result: ArchHypoResult,
        routing: RequestRouting,
        review_history: list[dict[str, object]],
        hitl_enabled: bool,
        chat_model: str | None,
        system_one_model: str | None,
    ) -> str: ...

    def get_by_id(self, artifact_id: str) -> ArchHypoArtifactRecord | None: ...

    def update_status(
        self,
        artifact_id: str,
        status: Literal["open", "closed"],
    ) -> ArchHypoArtifactRecord | None: ...

    def list(
        self,
        *,
        project_id: str | None = None,
        thread_id: str | None = None,
    ) -> list[ArchHypoArtifactRecord]: ...


class SQLiteArchHypoArtifactRepository:
    """Store queryable metadata alongside the exact structured result JSON."""

    _SELECT_COLUMNS = """
        id, cycle_id, thread_id, project_id, title, status, outcome,
        hitl_enabled, chat_model, system_one_model, result_schema_version,
        routing_json, review_history_json, result_json, created_at, updated_at
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def save_final_result(
        self,
        *,
        cycle_id: str,
        thread_id: str,
        project_id: str | None,
        result: ArchHypoResult,
        routing: RequestRouting,
        review_history: list[dict[str, object]],
        hitl_enabled: bool,
        chat_model: str | None,
        system_one_model: str | None,
    ) -> str:
        """Insert once, or return the existing ID for an identical retry."""

        if not cycle_id.strip() or not thread_id.strip():
            raise ValueError(
                "cycle_id and thread_id are required to persist an artifact"
            )

        result_json = result.model_dump_json()
        routing_json = routing.model_dump_json()
        review_history_json = json.dumps(review_history, ensure_ascii=False)
        created_at = _now()
        try:
            with self._connection:
                existing = self._connection.execute(
                    f"""SELECT {self._SELECT_COLUMNS}
                        FROM archhypo_artifacts WHERE cycle_id = ?""",
                    (cycle_id,),
                ).fetchone()
                if existing is not None:
                    record = _artifact_from_row(existing)
                    if not _same_snapshot(
                        record,
                        thread_id=thread_id,
                        project_id=project_id,
                        result_json=result_json,
                        routing_json=routing_json,
                        review_history_json=review_history_json,
                        hitl_enabled=hitl_enabled,
                        chat_model=chat_model,
                        system_one_model=system_one_model,
                    ):
                        raise ArtifactPersistenceError(
                            "The cycle ID already belongs to a different result "
                            "snapshot"
                        )
                    return record.id

                artifact_id = uuid4().hex
                self._connection.execute(
                    """
                    INSERT INTO archhypo_artifacts (
                        id, cycle_id, thread_id, project_id, title, status, outcome,
                        hitl_enabled, chat_model, system_one_model,
                        result_schema_version, routing_json, review_history_json,
                        result_json, created_at, updated_at
                    ) VALUES (
                        ?, ?, ?, ?, ?, 'open', 'not_evaluated', ?, ?, ?, 1,
                        ?, ?, ?, ?, ?
                    )
                    """,
                    (
                        artifact_id,
                        cycle_id,
                        thread_id,
                        project_id,
                        result.hypothesis.title,
                        int(hitl_enabled),
                        chat_model,
                        system_one_model,
                        routing_json,
                        review_history_json,
                        result_json,
                        created_at,
                        created_at,
                    ),
                )
                return artifact_id
        except sqlite3.Error as error:
            raise ArtifactPersistenceError(
                "Could not persist the final ArchHypo result"
            ) from error

    def get_by_id(self, artifact_id: str) -> ArchHypoArtifactRecord | None:
        row = self._connection.execute(
            f"SELECT {self._SELECT_COLUMNS} FROM archhypo_artifacts WHERE id = ?",
            (artifact_id,),
        ).fetchone()
        return _artifact_from_row(row) if row is not None else None

    def update_status(
        self,
        artifact_id: str,
        status: Literal["open", "closed"],
    ) -> ArchHypoArtifactRecord | None:
        if status not in {"open", "closed"}:
            raise ValueError("artifact status must be 'open' or 'closed'")

        try:
            with self._connection:
                cursor = self._connection.execute(
                    """UPDATE archhypo_artifacts
                       SET status = ?, updated_at = ?
                       WHERE id = ?""",
                    (status, _now(), artifact_id),
                )
                if cursor.rowcount == 0:
                    return None
                row = self._connection.execute(
                    f"SELECT {self._SELECT_COLUMNS} FROM archhypo_artifacts "
                    "WHERE id = ?",
                    (artifact_id,),
                ).fetchone()
        except sqlite3.Error as error:
            raise ArtifactPersistenceError(
                "Could not update the ArchHypo artifact status"
            ) from error

        return _artifact_from_row(row) if row is not None else None

    def list(
        self,
        *,
        project_id: str | None = None,
        thread_id: str | None = None,
    ) -> list[ArchHypoArtifactRecord]:
        filters: list[str] = []
        parameters: list[str] = []
        if project_id is not None:
            filters.append("project_id = ?")
            parameters.append(project_id)
        if thread_id is not None:
            filters.append("thread_id = ?")
            parameters.append(thread_id)
        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        rows = self._connection.execute(
            f"""SELECT {self._SELECT_COLUMNS} FROM archhypo_artifacts
                {where} ORDER BY created_at DESC, id""",
            parameters,
        ).fetchall()
        return [_artifact_from_row(row) for row in rows]


def _same_snapshot(
    record: ArchHypoArtifactRecord,
    *,
    thread_id: str,
    project_id: str | None,
    result_json: str,
    routing_json: str,
    review_history_json: str,
    hitl_enabled: bool,
    chat_model: str | None,
    system_one_model: str | None,
) -> bool:
    return (
        record.thread_id == thread_id
        and record.project_id == project_id
        and record.result == json.loads(result_json)
        and record.routing == json.loads(routing_json)
        and record.review_history == json.loads(review_history_json)
        and record.hitl_enabled == hitl_enabled
        and record.chat_model == chat_model
        and record.system_one_model == system_one_model
    )


def _artifact_from_row(row: sqlite3.Row | Sequence[object]) -> ArchHypoArtifactRecord:
    return ArchHypoArtifactRecord(
        id=str(row[0]),
        cycle_id=str(row[1]),
        thread_id=str(row[2]),
        project_id=str(row[3]) if row[3] is not None else None,
        title=str(row[4]),
        status=str(row[5]),
        outcome=str(row[6]),
        hitl_enabled=bool(row[7]),
        chat_model=str(row[8]) if row[8] is not None else None,
        system_one_model=str(row[9]) if row[9] is not None else None,
        result_schema_version=int(row[10]),
        routing=json.loads(str(row[11])),
        review_history=json.loads(str(row[12])),
        result=json.loads(str(row[13])),
        created_at=str(row[14]),
        updated_at=str(row[15]),
    )


def _now() -> str:
    return datetime.now(UTC).isoformat()


__all__ = [
    "ArchHypoArtifactRecord",
    "ArchHypoArtifactRepository",
    "ArtifactPersistenceError",
    "SQLiteArchHypoArtifactRepository",
]
