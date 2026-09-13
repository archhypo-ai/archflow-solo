"""SQLite checkpointer lifecycle for the local ArchWise runtime."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

from .migrations import migrate_connection
from .paths import CHECKPOINT_DB_PATH


def open_sqlite_checkpointer(
    path: Path = CHECKPOINT_DB_PATH,
) -> tuple[SqliteSaver, sqlite3.Connection]:
    """Open and initialize a SQLite checkpointer.

    The caller must retain the connection for the complete graph lifetime and
    close it when the application runtime stops.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(
        path,
        timeout=30,
        check_same_thread=False,
    )
    try:
        migrate_connection(connection)
        checkpointer = SqliteSaver(connection)
        checkpointer.setup()
    except Exception:
        connection.close()
        raise
    return checkpointer, connection


__all__ = ["open_sqlite_checkpointer"]
