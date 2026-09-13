"""SQLite checkpointer lifecycle and persistence coordination."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

from .conversations import SQLiteConversationRepository
from .migrations import migrate_connection
from .paths import CHECKPOINT_DB_PATH


class TransactionalSqliteSaver(SqliteSaver):
    """SQLite saver with a deletion operation that can join a transaction."""

    def delete_thread_without_commit(self, thread_id: str) -> None:
        """Delete checkpoint rows without committing the current transaction."""

        with self.cursor(transaction=False) as cursor:
            cursor.execute(
                "DELETE FROM checkpoints WHERE thread_id = ?",
                (str(thread_id),),
            )
            cursor.execute(
                "DELETE FROM writes WHERE thread_id = ?",
                (str(thread_id),),
            )


@dataclass(slots=True)
class SQLitePersistence:
    """Own the shared connection and coordinate SQLite-backed components."""

    checkpointer: TransactionalSqliteSaver
    connection: sqlite3.Connection
    conversations: SQLiteConversationRepository

    def delete_thread(self, thread_id: str) -> None:
        """Delete graph state and metadata in one SQLite transaction."""

        with self.connection:
            self.checkpointer.delete_thread_without_commit(thread_id)
            self.conversations.delete(thread_id, commit=False)

    def close(self) -> None:
        """Close the connection owned by this persistence runtime."""

        self.connection.close()


def open_sqlite_persistence(
    path: Path = CHECKPOINT_DB_PATH,
) -> SQLitePersistence:
    """Open and initialize the local SQLite persistence runtime."""

    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(
        path,
        timeout=30,
        check_same_thread=False,
    )
    try:
        migrate_connection(connection)
        checkpointer = TransactionalSqliteSaver(connection)
        checkpointer.setup()
        conversations = SQLiteConversationRepository(connection)
    except Exception:
        connection.close()
        raise

    return SQLitePersistence(
        checkpointer=checkpointer,
        connection=connection,
        conversations=conversations,
    )


def open_sqlite_checkpointer(
    path: Path = CHECKPOINT_DB_PATH,
) -> tuple[TransactionalSqliteSaver, sqlite3.Connection]:
    """Open a SQLite saver for callers that only need the checkpointer."""

    persistence = open_sqlite_persistence(path)
    return persistence.checkpointer, persistence.connection


__all__ = [
    "SQLitePersistence",
    "TransactionalSqliteSaver",
    "open_sqlite_checkpointer",
    "open_sqlite_persistence",
]
