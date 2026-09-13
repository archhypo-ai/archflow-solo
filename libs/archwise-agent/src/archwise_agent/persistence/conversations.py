"""SQLite catalog for user-facing conversation metadata."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime

DEFAULT_CONVERSATION_TITLE = "Untitled conversation"


@dataclass(frozen=True, slots=True)
class ConversationMetadata:
    """Metadata stored separately from the graph transcript and state."""

    thread_id: str
    title: str
    created_at: str
    updated_at: str
    pinned: bool


class ConversationCatalog:
    """Persist conversation metadata using the checkpointer connection."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def list(self) -> list[ConversationMetadata]:
        rows = self._connection.execute(
            """
            SELECT thread_id, title, created_at, updated_at, pinned
            FROM conversations
            ORDER BY pinned DESC, updated_at DESC
            """
        ).fetchall()
        return [_metadata_from_row(row) for row in rows]

    def get(self, thread_id: str) -> ConversationMetadata | None:
        row = self._connection.execute(
            """
            SELECT thread_id, title, created_at, updated_at, pinned
            FROM conversations
            WHERE thread_id = ?
            """,
            (thread_id,),
        ).fetchone()
        return _metadata_from_row(row) if row else None

    def delete(self, thread_id: str) -> bool:
        """Delete conversation metadata and report whether it existed."""

        cursor = self._connection.execute(
            "DELETE FROM conversations WHERE thread_id = ?",
            (thread_id,),
        )
        self._connection.commit()
        return cursor.rowcount > 0

    def ensure(
        self,
        thread_id: str,
        title: str | None = None,
    ) -> ConversationMetadata:
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
                UPDATE conversations
                SET title = ?, updated_at = ?
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
            raise RuntimeError("Conversation catalog entry was not created")
        return metadata


def _metadata_from_row(row: sqlite3.Row | tuple[object, ...]) -> ConversationMetadata:
    return ConversationMetadata(
        thread_id=str(row[0]),
        title=str(row[1]),
        created_at=str(row[2]),
        updated_at=str(row[3]),
        pinned=bool(row[4]),
    )


def _clean_title(value: str | None) -> str:
    if not value:
        return DEFAULT_CONVERSATION_TITLE
    compact = " ".join(value.split())
    return compact[:80].rstrip() or DEFAULT_CONVERSATION_TITLE


def _now() -> str:
    return datetime.now(UTC).isoformat()


__all__ = [
    "ConversationCatalog",
    "ConversationMetadata",
    "DEFAULT_CONVERSATION_TITLE",
]
