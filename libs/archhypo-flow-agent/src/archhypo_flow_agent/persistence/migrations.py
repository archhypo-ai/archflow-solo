"""Versioned schema migrations for local conversation metadata."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

MIGRATIONS_TABLE = "archhypo_flow_schema_migrations"
CURRENT_SCHEMA_VERSION = 1


def migrate_connection(connection: sqlite3.Connection) -> None:
    """Create or upgrade the ArchHypo Flow tables on an open connection."""

    connection.execute("PRAGMA busy_timeout = 30000")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {MIGRATIONS_TABLE} (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
            """
        )
        row = connection.execute(
            f"SELECT COALESCE(MAX(version), 0) FROM {MIGRATIONS_TABLE}"
        ).fetchone()
        version = int(row[0]) if row else 0
        if version > CURRENT_SCHEMA_VERSION:
            raise RuntimeError(
                f"Database schema version {version} is newer than supported "
                f"version {CURRENT_SCHEMA_VERSION}."
            )

        if version < 1:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    icon TEXT NOT NULL,
                    color TEXT NOT NULL,
                    instructions TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    thread_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    pinned INTEGER NOT NULL DEFAULT 0
                        CHECK (pinned IN (0, 1)),
                    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_conversations_updated_at
                ON conversations (pinned DESC, updated_at DESC)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_conversations_project_id
                ON conversations (project_id)
                """
            )
            connection.execute(
                f"INSERT INTO {MIGRATIONS_TABLE} (version, applied_at) VALUES (?, ?)",
                (1, datetime.now(UTC).isoformat()),
            )

        connection.commit()
    except Exception:
        connection.rollback()
        raise


__all__ = ["CURRENT_SCHEMA_VERSION", "MIGRATIONS_TABLE", "migrate_connection"]
