"""SQLite checkpoint and conversation metadata lifecycle."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

from archhypo_flow_agent.persistence.conversations import SQLiteConversationRepository
from archhypo_flow_agent.persistence.migrations import migrate_connection
from archhypo_flow_agent.persistence.paths import DATABASE_PATH
from archhypo_flow_agent.persistence.projects import SQLiteProjectRepository


@dataclass(slots=True)
class SQLitePersistence:
    """Own the shared database connection and its persistence adapters."""

    connection: sqlite3.Connection
    checkpointer: SqliteSaver
    conversations: SQLiteConversationRepository
    projects: SQLiteProjectRepository

    def delete_project(self, project_id: str) -> bool:
        """Delete a project, its conversations, and their checkpoint state."""

        with self.connection:
            with self.checkpointer.cursor(transaction=False) as cursor:
                for table in ("checkpoints", "writes"):
                    cursor.execute(
                        f"""
                        DELETE FROM {table}
                        WHERE thread_id IN (
                            SELECT thread_id FROM conversations WHERE project_id = ?
                        )
                        """,
                        (project_id,),
                    )
            cursor = self.connection.execute(
                "DELETE FROM projects WHERE id = ?",
                (project_id,),
            )
            return cursor.rowcount > 0

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
        projects = SQLiteProjectRepository(connection)
    except Exception:
        connection.close()
        raise

    return SQLitePersistence(
        connection=connection,
        checkpointer=checkpointer,
        conversations=conversations,
        projects=projects,
    )


__all__ = ["SQLitePersistence", "open_sqlite_persistence"]
