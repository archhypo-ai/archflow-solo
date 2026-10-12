import sqlite3

from archhypo_flow_agent.core import ChatRequest
from archhypo_flow_agent.persistence.schema import initialize_schema
from archhypo_flow_agent.services import AgentService
from tests.fakes import stub_chat_model


def test_initial_schema_is_idempotent_without_migrations(tmp_path) -> None:
    database_path = tmp_path / "runtime" / "conversations.sqlite"
    database_path.parent.mkdir(parents=True)

    with sqlite3.connect(database_path) as connection:
        initialize_schema(connection)
        initialize_schema(connection)
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert "projects" in tables
    assert "conversations" in tables
    assert "global_context" not in tables
    assert "archhypo_flow_schema_migrations" not in tables
    assert "checkpoints" not in tables
    with sqlite3.connect(database_path) as connection:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(conversations)")
        }
    assert "project_id" in columns


def test_chat_transcript_survives_service_restart(tmp_path) -> None:
    database_path = tmp_path / "runtime" / "conversations.sqlite"
    first_service = AgentService(model=stub_chat_model(), database_path=database_path)
    first_service.respond(
        ChatRequest(thread_id="persisted-thread", message="Remember this")
    )
    first_service.respond(ChatRequest(thread_id="persisted-thread", message="Continue"))
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


def test_project_delete_cascades_to_conversations_and_checkpoints(tmp_path) -> None:
    service = AgentService(
        model=stub_chat_model(), database_path=tmp_path / "projects.sqlite"
    )
    try:
        service.respond(ChatRequest(thread_id="project-thread", message="Hello"))
        initial = service.get_conversation("project-thread")
        assert initial is not None
        assert initial.project_id is None

        service.create_project(
            project_id="project-1",
            name="Architecture",
            icon="folder",
            color="blue",
            instructions="Prefer simple designs.",
        )
        assigned = service.set_conversation_project("project-thread", "project-1")
        assert assigned is not None
        assert assigned.project_id == "project-1"
        assert len(service.list_projects()) == 1

        assert service.delete_project("project-1") is True
        assert service.get_conversation("project-thread") is None
        assert service.list_conversations() == []
    finally:
        service.close()

    with sqlite3.connect(tmp_path / "projects.sqlite") as connection:
        checkpoint_count = connection.execute(
            "SELECT COUNT(*) FROM checkpoints WHERE thread_id = ?",
            ("project-thread",),
        ).fetchone()[0]
        write_count = connection.execute(
            "SELECT COUNT(*) FROM writes WHERE thread_id = ?",
            ("project-thread",),
        ).fetchone()[0]
    assert checkpoint_count == 0
    assert write_count == 0


def test_conversation_update_and_delete_remove_checkpoint_state(tmp_path) -> None:
    database_path = tmp_path / "runtime" / "conversations.sqlite"
    service = AgentService(model=stub_chat_model(), database_path=database_path)
    try:
        service.respond(
            ChatRequest(thread_id="managed-thread", message="Keep this briefly")
        )
        updated = service.update_conversation(
            "managed-thread",
            title="Renamed conversation",
            pinned=True,
        )
        assert updated is not None
        assert updated.title == "Renamed conversation"
        assert updated.pinned is True
        assert service.delete_conversation("managed-thread") is True
        assert service.delete_conversation("managed-thread") is False
        assert service.list_conversations() == []
        assert service.get_conversation("managed-thread") is None
    finally:
        service.close()

    with sqlite3.connect(database_path) as connection:
        checkpoint_count = connection.execute(
            "SELECT COUNT(*) FROM checkpoints WHERE thread_id = ?",
            ("managed-thread",),
        ).fetchone()[0]
        write_count = connection.execute(
            "SELECT COUNT(*) FROM writes WHERE thread_id = ?",
            ("managed-thread",),
        ).fetchone()[0]

    assert checkpoint_count == 0
    assert write_count == 0


def test_sqlite_stores_graph_checkpoints_and_conversation_metadata(tmp_path) -> None:
    database_path = tmp_path / "runtime" / "conversations.sqlite"
    service = AgentService(model=stub_chat_model(), database_path=database_path)
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
