from io import BytesIO

from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import InMemorySaver

from archwise_agent import AgentService
from archwise_agent.backend import create_app
from tests.fakes import fake_hypothesis_model


def test_threads_controller_lists_and_loads_conversations() -> None:
    service = AgentService(
        model=fake_hypothesis_model(["first reply", "second reply"]),
        checkpointer=InMemorySaver(),
    )

    with TestClient(create_app(service)) as client:
        first = client.post(
            "/api/chat",
            json={"thread_id": "thread-a", "message": "First question"},
        )
        second = client.post(
            "/api/chat",
            json={"thread_id": "thread-a", "message": "Second question"},
        )
        listing = client.get("/api/threads")
        detail = client.get("/api/threads/thread-a")

    assert first.status_code == 200
    assert second.status_code == 200
    assert listing.status_code == 200
    assert listing.json() == [
        {
            "thread_id": "thread-a",
            "title": "First question",
            "message_count": 4,
            "pinned": False,
        }
    ]
    assert detail.status_code == 200
    assert detail.json() == {
        "thread_id": "thread-a",
        "title": "First question",
        "message_count": 4,
        "messages": [
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "ArchWise response."},
            {"role": "user", "content": "Second question"},
            {"role": "assistant", "content": "ArchWise response."},
        ],
        "pinned": False,
        "folder_context": None,
    }


def test_threads_controller_persists_a_folder_context(tmp_path) -> None:
    service = AgentService(
        model=fake_hypothesis_model(["unused"]),
        database_path=tmp_path / "checkpoints.sqlite",
    )

    try:
        with TestClient(create_app(service)) as client:
            attached = client.post(
                "/api/threads/thread-folder/folder-context",
                data={"folder_name": "sample-project"},
                files=[
                    (
                        "files",
                        (
                            "sample-project/src/main.py",
                            b"print('hello')",
                            "text/x-python",
                        ),
                    ),
                    (
                        "files",
                        (
                            "sample-project/README.md",
                            b"# Sample",
                            "text/markdown",
                        ),
                    ),
                ],
            )
            loaded = client.get("/api/threads/thread-folder")
            listing = client.get("/api/threads")

        assert attached.status_code == 200
        assert attached.json()["folder_name"] == "sample-project"
        assert attached.json()["file_count"] == 2
        assert loaded.status_code == 200
        assert loaded.json()["messages"] == []
        assert loaded.json()["folder_context"] == attached.json()
        assert listing.json()[0]["thread_id"] == "thread-folder"
    finally:
        service.delete_folder_context("thread-folder")
        service.close()


def test_threads_controller_attaches_a_native_folder_path(tmp_path) -> None:
    folder = tmp_path / "native-project"
    (folder / "src").mkdir(parents=True)
    (folder / "src" / "main.py").write_text("print('ok')")
    service = AgentService(
        model=fake_hypothesis_model(["unused"]),
        database_path=tmp_path / "checkpoints.sqlite",
    )

    try:
        with TestClient(create_app(service)) as client:
            attached = client.post(
                "/api/threads/thread-native/folder-context/path",
                json={"folder_path": str(folder)},
            )
            loaded = client.get("/api/threads/thread-native")

        assert attached.status_code == 200
        assert attached.json()["folder_name"] == "native-project"
        assert attached.json()["file_count"] == 1
        assert loaded.json()["folder_context"] == attached.json()
    finally:
        service.delete_folder_context("thread-native")
        service.close()


def test_folder_context_survives_service_restart(tmp_path) -> None:
    database_path = tmp_path / "checkpoints.sqlite"
    first_service = AgentService(
        model=fake_hypothesis_model(["unused"]),
        database_path=database_path,
    )
    first_service.attach_folder_context(
        thread_id="restart-folder",
        folder_name="restart-project",
        files=[("restart-project/app.py", BytesIO(b"print('ok')"))],
    )
    first_service.close()

    second_service = AgentService(
        model=fake_hypothesis_model(["unused"]),
        database_path=database_path,
    )
    try:
        context = second_service.get_folder_context("restart-folder")
        conversation = second_service.get_conversation("restart-folder")
        assert context is not None
        assert context.folder_name == "restart-project"
        assert context.file_count == 1
        assert conversation is not None
        assert conversation.folder_context == context
    finally:
        second_service.delete_folder_context("restart-folder")
        second_service.close()


def test_threads_controller_deletes_a_conversation() -> None:
    service = AgentService(
        model=fake_hypothesis_model(["reply"]),
        checkpointer=InMemorySaver(),
    )

    with TestClient(create_app(service)) as client:
        created = client.post(
            "/api/chat",
            json={"thread_id": "thread-to-delete", "message": "Delete me"},
        )
        deleted = client.delete("/api/threads/thread-to-delete")
        listing = client.get("/api/threads")
        detail = client.get("/api/threads/thread-to-delete")

    assert created.status_code == 200
    assert deleted.status_code == 204
    assert listing.json() == []
    assert detail.status_code == 404


def test_threads_controller_updates_pinned_state(tmp_path) -> None:
    service = AgentService(
        model=fake_hypothesis_model(["reply"]),
        database_path=tmp_path / "checkpoints.sqlite",
    )

    try:
        with TestClient(create_app(service)) as client:
            client.post(
                "/api/chat",
                json={"thread_id": "thread-to-pin", "message": "Pin me"},
            )
            pinned = client.patch(
                "/api/threads/thread-to-pin",
                json={"pinned": True},
            )
            listing = client.get("/api/threads")
            unpinned = client.patch(
                "/api/threads/thread-to-pin",
                json={"pinned": False},
            )
    finally:
        service.close()

    assert pinned.status_code == 200
    assert pinned.json()["pinned"] is True
    assert listing.json()[0]["pinned"] is True
    assert unpinned.status_code == 200
    assert unpinned.json()["pinned"] is False


def test_threads_controller_rejects_empty_update() -> None:
    service = AgentService(
        model=fake_hypothesis_model(["unused"]),
        checkpointer=InMemorySaver(),
    )

    with TestClient(create_app(service)) as client:
        response = client.patch("/api/threads/unknown", json={})

    assert response.status_code == 422


def test_threads_controller_returns_not_found_for_unknown_thread() -> None:
    service = AgentService(
        model=fake_hypothesis_model(["unused"]),
        checkpointer=InMemorySaver(),
    )

    with TestClient(create_app(service)) as client:
        response = client.get("/api/threads/unknown")
        delete_response = client.delete("/api/threads/unknown")

    assert response.status_code == 404
    assert delete_response.status_code == 404
