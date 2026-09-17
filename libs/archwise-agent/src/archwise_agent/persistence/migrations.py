"""Versioned migrations for the shared ArchWise SQLite database."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

MigrationOperation = Callable[[sqlite3.Connection], None]


@dataclass(frozen=True, slots=True)
class Migration:
    """One ordered database schema migration."""

    version: int
    name: str
    apply: MigrationOperation


CURRENT_SCHEMA_VERSION = 1
_MIGRATIONS_TABLE = "archwise_schema_migrations"


def _migration_1_create_conversation_catalog(
    connection: sqlite3.Connection,
) -> None:
    """Create metadata storage without duplicating graph checkpoint state."""

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            thread_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            pinned INTEGER NOT NULL DEFAULT 0 CHECK (pinned IN (0, 1))
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_conversations_updated_at
          ON conversations (updated_at DESC)
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS folder_contexts (
            context_id TEXT PRIMARY KEY,
            thread_id TEXT NOT NULL UNIQUE,
            folder_name TEXT NOT NULL,
            file_count INTEGER NOT NULL CHECK (file_count > 0),
            total_bytes INTEGER NOT NULL CHECK (total_bytes >= 0),
            storage_path TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (thread_id) REFERENCES conversations(thread_id)
                ON DELETE CASCADE
        )
        """
    )


MIGRATIONS: tuple[Migration, ...] = (
    Migration(
        version=1,
        name="create_conversation_catalog",
        apply=_migration_1_create_conversation_catalog,
    ),
)


def migrate_database(path: Path) -> None:
    """Apply all pending ArchWise migrations to ``path``."""

    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=30)
    try:
        _configure_connection(connection)
        migrate_connection(connection)
    finally:
        connection.close()


def migrate_connection(connection: sqlite3.Connection) -> None:
    """Apply pending migrations using an already-open SQLite connection."""

    _configure_connection(connection)
    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {_MIGRATIONS_TABLE} (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
            """
        )
        current_version = _current_version(connection)
        if current_version > CURRENT_SCHEMA_VERSION:
            raise RuntimeError(
                "Database schema version "
                f"{current_version} is newer than supported version "
                f"{CURRENT_SCHEMA_VERSION}."
            )

        for migration in MIGRATIONS:
            if migration.version <= current_version:
                continue
            migration.apply(connection)
            connection.execute(
                f"""
                INSERT INTO {_MIGRATIONS_TABLE} (version, name, applied_at)
                VALUES (?, ?, ?)
                """,
                (migration.version, migration.name, _now()),
            )
            current_version = migration.version

        connection.commit()
    except Exception:
        connection.rollback()
        raise


def _configure_connection(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA busy_timeout = 30000")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA foreign_keys = ON")


def _current_version(connection: sqlite3.Connection) -> int:
    row = connection.execute(
        f"SELECT COALESCE(MAX(version), 0) FROM {_MIGRATIONS_TABLE}"
    ).fetchone()
    return int(row[0]) if row else 0


def _now() -> str:
    return datetime.now(UTC).isoformat()


__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "MIGRATIONS",
    "Migration",
    "migrate_connection",
    "migrate_database",
]
