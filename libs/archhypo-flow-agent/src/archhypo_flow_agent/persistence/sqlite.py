"""SQLite checkpoint and conversation metadata lifecycle."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

from archhypo_flow_agent.persistence.conversations import SQLiteConversationRepository
from archhypo_flow_agent.persistence.migrations import migrate_connection
from archhypo_flow_agent.persistence.paths import DATABASE_PATH


@dataclass(slots=True)
class SQLitePersistence:
    """Own the shared database connection and its persistence adapters."""

    connection: sqlite3.Connection
    checkpointer: SqliteSaver
    conversations: SQLiteConversationRepository

    def delete_thread(self, thread_id: str) -> bool:
        """Delete checkpoint state and metadata in one SQLite transaction."""

        with self.connection:
            with self.checkpointer.cursor(transaction=False) as cursor:
                cursor.execute(
                    "DELETE FROM checkpoints WHERE thread_id = ?",
                    (thread_id,),
                )
                cursor.execute(
                    "DELETE FROM writes WHERE thread_id = ?",
                    (thread_id,),
                )
            return self.conversations.delete(thread_id, commit=False)

    def close(self) -> None:
        self.connection.close()


def open_sqlite_persistence(path: Path = DATABASE_PATH) -> SQLitePersistence:
    """Open the local database, applying metadata and LangGraph schemas."""

    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=30, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    try:
        migrate_connection(connection)
        checkpointer = SqliteSaver(connection)
        checkpointer.setup()
        conversations = SQLiteConversationRepository(connection)
    except Exception:
        connection.close()
        raise

    return SQLitePersistence(
        connection=connection,
        checkpointer=checkpointer,
        conversations=conversations,
    )


__all__ = ["SQLitePersistence", "open_sqlite_persistence"]
