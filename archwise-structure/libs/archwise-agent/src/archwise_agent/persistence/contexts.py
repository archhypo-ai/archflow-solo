"""SQLite repository for persisted folder contexts."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class FolderContextMetadata:
    """Storage metadata for one folder attached to a conversation."""

    context_id: str
    thread_id: str
    folder_name: str
    file_count: int
    total_bytes: int
    storage_path: str
    created_at: str


class FolderContextRepository(Protocol):
    """Persistence contract for conversation folder contexts."""

    def get(self, thread_id: str) -> FolderContextMetadata | None: ...

    def list(self) -> list[FolderContextMetadata]: ...

    def replace(self, context: FolderContextMetadata) -> None: ...

    def delete(self, thread_id: str) -> FolderContextMetadata | None: ...


class SQLiteFolderContextRepository:
    """Persist one replaceable folder context per conversation."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def get(self, thread_id: str) -> FolderContextMetadata | None:
        row = self._connection.execute(
            """
            SELECT context_id, thread_id, folder_name, file_count,
                   total_bytes, storage_path, created_at
            FROM folder_contexts
            WHERE thread_id = ?
            """,
            (thread_id,),
        ).fetchone()
        return _context_from_row(row) if row else None

    def list(self) -> list[FolderContextMetadata]:
        rows = self._connection.execute(
            """
            SELECT context_id, thread_id, folder_name, file_count,
                   total_bytes, storage_path, created_at
            FROM folder_contexts
            ORDER BY created_at DESC
            """
        ).fetchall()
        return [_context_from_row(row) for row in rows]

    def replace(self, context: FolderContextMetadata) -> None:
        self._connection.execute(
            "DELETE FROM folder_contexts WHERE thread_id = ?",
            (context.thread_id,),
        )
        self._connection.execute(
            """
            INSERT INTO folder_contexts (
                context_id, thread_id, folder_name, file_count,
                total_bytes, storage_path, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                context.context_id,
                context.thread_id,
                context.folder_name,
                context.file_count,
                context.total_bytes,
                context.storage_path,
                context.created_at,
            ),
        )
        self._connection.commit()

    def delete(self, thread_id: str) -> FolderContextMetadata | None:
        context = self.get(thread_id)
        if context is None:
            return None
        self._connection.execute(
            "DELETE FROM folder_contexts WHERE thread_id = ?",
            (thread_id,),
        )
        self._connection.commit()
        return context


def _context_from_row(row: sqlite3.Row | tuple[object, ...]) -> FolderContextMetadata:
    return FolderContextMetadata(
        context_id=str(row[0]),
        thread_id=str(row[1]),
        folder_name=str(row[2]),
        file_count=int(row[3]),
        total_bytes=int(row[4]),
        storage_path=str(row[5]),
        created_at=str(row[6]),
    )


__all__ = [
    "FolderContextMetadata",
    "FolderContextRepository",
    "SQLiteFolderContextRepository",
]
