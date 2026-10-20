"""Initial SQLite schema for the local ArchHypo Flow runtime."""

from __future__ import annotations

import sqlite3


def initialize_schema(connection: sqlite3.Connection) -> None:
    """Create the current local schema without versioned migrations."""

    connection.execute("PRAGMA busy_timeout = 30000")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA foreign_keys = ON")
    with connection:
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
            """
            CREATE TABLE IF NOT EXISTS archhypo_artifacts (
                id TEXT PRIMARY KEY,
                cycle_id TEXT NOT NULL UNIQUE,
                thread_id TEXT NOT NULL,
                project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                outcome TEXT NOT NULL DEFAULT 'not_evaluated',
                hitl_enabled INTEGER NOT NULL CHECK (hitl_enabled IN (0, 1)),
                chat_model TEXT,
                system_one_model TEXT,
                result_schema_version INTEGER NOT NULL,
                routing_json TEXT NOT NULL,
                review_history_json TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_archhypo_artifacts_project_created
            ON archhypo_artifacts (project_id, created_at DESC)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_archhypo_artifacts_thread_created
            ON archhypo_artifacts (thread_id, created_at DESC)
            """
        )
__all__ = ["initialize_schema"]
