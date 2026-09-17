import sqlite3

from archwise_agent import AgentService
from archwise_agent.persistence import (
    CURRENT_SCHEMA_VERSION,
    migrate_database,
)
from tests.fakes import archhypo_json, fake_hypothesis_model


def test_migrations_are_idempotent(tmp_path) -> None:
    database_path = tmp_path / "runtime" / "checkpoints.sqlite"

    migrate_database(database_path)
    migrate_database(database_path)

    with sqlite3.connect(database_path) as connection:
        version = connection.execute(
            "SELECT MAX(version) FROM archwise_schema_migrations"
        ).fetchone()[0]
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert version == CURRENT_SCHEMA_VERSION
    assert "archwise_schema_migrations" in tables
    assert "conversations" in tables


def test_sqlite_checkpoints_survive_service_restart(tmp_path) -> None:
    database_path = tmp_path / "runtime" / "checkpoints.sqlite"

    first_service = AgentService(
        model=fake_hypothesis_model(["persistent reply"]),
        database_path=database_path,
    )
    first_service.send(thread_id="persistent-thread", message="Remember this")
    first_service.close()

    second_service = AgentService(
        model=fake_hypothesis_model(["unused"]),
        database_path=database_path,
    )
    try:
        conversations = second_service.list_conversations()
        conversation = second_service.get_conversation("persistent-thread")
    finally:
        second_service.close()

    assert conversations[0].thread_id == "persistent-thread"
    assert conversations[0].title == "Remember this"
    assert conversation is not None
    assert [message.content for message in conversation.messages] == [
        "Remember this",
        archhypo_json("Remember this", "persistent reply"),
    ]


def test_sqlite_delete_removes_checkpoint_and_catalog_entry(tmp_path) -> None:
    database_path = tmp_path / "runtime" / "checkpoints.sqlite"
    service = AgentService(
        model=fake_hypothesis_model(["reply"]),
        database_path=database_path,
    )

    try:
        service.send(thread_id="thread-to-delete", message="Delete me")
        assert service.delete_conversation("thread-to-delete") is True
        assert service.list_conversations() == []
        assert service.get_conversation("thread-to-delete") is None
        assert service.delete_conversation("thread-to-delete") is False
    finally:
        service.close()
