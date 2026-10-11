"""Conversation metadata contracts and SQLite repository."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

DEFAULT_CONVERSATION_TITLE = "Untitled conversation"


@dataclass(frozen=True, slots=True)
class ConversationMetadata:
    thread_id: str
    title: str
    created_at: str
    updated_at: str
    pinned: bool
    project_id: str | None


class ConversationRepository(Protocol):
    def list(self) -> list[ConversationMetadata]: ...

    def get(self, thread_id: str) -> ConversationMetadata | None: ...

    def ensure(
        self,
        thread_id: str,
        title: str | None = None,
    ) -> ConversationMetadata: ...

    def update(
        self,
        thread_id: str,
        *,
        title: str | None = None,
        pinned: bool | None = None,
    ) -> ConversationMetadata | None: ...

    def set_project(
        self,
        thread_id: str,
        project_id: str | None,
    ) -> ConversationMetadata | None: ...

    def delete(self, thread_id: str, *, commit: bool = True) -> bool: ...


class SQLiteConversationRepository:
    """Persist conversation titles and activity in the shared SQLite database."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def list(self) -> list[ConversationMetadata]:
        rows = self._connection.execute(
            """
            SELECT thread_id, title, created_at, updated_at, pinned, project_id
            FROM conversations
            ORDER BY pinned DESC, updated_at DESC
            """
        ).fetchall()
        return [_metadata_from_row(row) for row in rows]

    def get(self, thread_id: str) -> ConversationMetadata | None:
        row = self._connection.execute(
            """
            SELECT thread_id, title, created_at, updated_at, pinned, project_id
            FROM conversations
            WHERE thread_id = ?
            """,
            (thread_id,),
        ).fetchone()
        return _metadata_from_row(row) if row else None

    def ensure(self, thread_id: str, title: str | None = None) -> ConversationMetadata:
        now = _now()
        clean_title = _clean_title(title)
        row = self._connection.execute(
            "SELECT title FROM conversations WHERE thread_id = ?",
            (thread_id,),
        ).fetchone()

        if row is None:
            self._connection.execute(
                """
                INSERT INTO conversations (thread_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (thread_id, clean_title, now, now),
            )
        elif row[0] == DEFAULT_CONVERSATION_TITLE and title:
            self._connection.execute(
                """
                UPDATE conversations SET title = ?, updated_at = ?
                WHERE thread_id = ?
                """,
                (clean_title, now, thread_id),
            )
        else:
            self._connection.execute(
                "UPDATE conversations SET updated_at = ? WHERE thread_id = ?",
                (now, thread_id),
            )

        self._connection.commit()
        metadata = self.get(thread_id)
        if metadata is None:
            raise RuntimeError("Conversation metadata was not created")
        return metadata

    def update(
        self,
        thread_id: str,
        *,
        title: str | None = None,
        pinned: bool | None = None,
    ) -> ConversationMetadata | None:
        current = self.get(thread_id)
        if current is None:
            return None

        assignments: list[str] = []
        values: list[object] = []
        if title is not None:
            clean_title = _clean_title(title)
            assignments.append("title = ?")
            values.append(clean_title)
        if pinned is not None:
            assignments.append("pinned = ?")
            values.append(int(pinned))
        if not assignments:
            return current

        assignments.append("updated_at = ?")
        values.extend((_now(), thread_id))
        self._connection.execute(
            f"UPDATE conversations SET {', '.join(assignments)} WHERE thread_id = ?",
            values,
        )
        self._connection.commit()
        return self.get(thread_id)

    def set_project(
        self,
        thread_id: str,
        project_id: str | None,
    ) -> ConversationMetadata | None:
        if self.get(thread_id) is None:
            return None
        self._connection.execute(
            """
            UPDATE conversations
            SET project_id = ?, updated_at = ?
            WHERE thread_id = ?
            """,
            (project_id, _now(), thread_id),
        )
        self._connection.commit()
        return self.get(thread_id)

    def delete(self, thread_id: str, *, commit: bool = True) -> bool:
        cursor = self._connection.execute(
            "DELETE FROM conversations WHERE thread_id = ?",
            (thread_id,),
        )
        if commit:
            self._connection.commit()
        return cursor.rowcount > 0


def _metadata_from_row(row: sqlite3.Row | tuple[object, ...]) -> ConversationMetadata:
    return ConversationMetadata(
        thread_id=str(row[0]),
        title=str(row[1]),
        created_at=str(row[2]),
        updated_at=str(row[3]),
        pinned=bool(row[4]),
        project_id=str(row[5]) if row[5] is not None else None,
    )


def _clean_title(value: str | None) -> str:
    if not value:
        return DEFAULT_CONVERSATION_TITLE
    compact = " ".join(value.split())
    return compact[:80].rstrip() or DEFAULT_CONVERSATION_TITLE


def _now() -> str:
    return datetime.now(UTC).isoformat()


__all__ = [
    "ConversationMetadata",
    "ConversationRepository",
    "DEFAULT_CONVERSATION_TITLE",
    "SQLiteConversationRepository",
]
