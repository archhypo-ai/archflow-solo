import sqlite3

from archhypo_flow_agent.core import ChatRequest
from archhypo_flow_agent.persistence.migrations import (
    CURRENT_SCHEMA_VERSION,
    migrate_connection,
)
from archhypo_flow_agent.services import AgentService


def test_schema_migration_is_idempotent(tmp_path) -> None:
    database_path = tmp_path / "runtime" / "conversations.sqlite"
    database_path.parent.mkdir(parents=True)

    with sqlite3.connect(database_path) as connection:
        migrate_connection(connection)
        migrate_connection(connection)
        version = connection.execute(
            "SELECT MAX(version) FROM archhypo_flow_schema_migrations"
        ).fetchone()[0]
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert version == CURRENT_SCHEMA_VERSION
    assert "conversations" in tables
    assert "checkpoints" not in tables


def test_chat_transcript_survives_service_restart(tmp_path) -> None:
    database_path = tmp_path / "runtime" / "conversations.sqlite"
    first_service = AgentService(database_path=database_path)
    first_service.respond(
        ChatRequest(thread_id="persisted-thread", message="Remember this")
    )
    first_service.respond(
        ChatRequest(thread_id="persisted-thread", message="Continue")
    )
    first_service.close()

    second_service = AgentService(database_path=database_path)
    try:
        conversations = second_service.list_conversations()
        conversation = second_service.get_conversation("persisted-thread")
    finally:
        second_service.close()

    assert len(conversations) == 1
    assert conversations[0].title == "Remember this"
    assert conversations[0].message_count == 4
    assert conversation is not None
    assert [message.content for message in conversation.messages] == [
        "Remember this",
        "Understood. Let's explore this architectural decision.",
        "Continue",
        "Understood. Let's explore this architectural decision.",
    ]


def test_sqlite_stores_graph_checkpoints_and_conversation_metadata(tmp_path) -> None:
    database_path = tmp_path / "runtime" / "conversations.sqlite"
    service = AgentService(database_path=database_path)
    try:
        service.respond(
            ChatRequest(thread_id="visible-thread", message="A visible message")
        )
    finally:
        service.close()

    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        title = connection.execute(
            "SELECT title FROM conversations WHERE thread_id = ?",
            ("visible-thread",),
        ).fetchone()[0]

    assert "conversations" in tables
    assert "checkpoints" in tables
    assert title == "A visible message"
