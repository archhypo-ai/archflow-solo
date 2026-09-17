from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import InMemorySaver

from archwise_agent import AgentService
from archwise_agent.backend import create_app
from tests.fakes import (
    classification_json,
    fake_hypothesis_model,
    hypothesis_json,
    technical_plan_json,
)


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
            "message_count": 8,
            "pinned": False,
        }
    ]
    assert detail.status_code == 200
    assert detail.json() == {
        "thread_id": "thread-a",
        "title": "First question",
        "message_count": 8,
        "messages": [
            {"role": "user", "content": "First question"},
            {
                "role": "assistant",
                "content": hypothesis_json("First question", "first reply"),
            },
            {"role": "assistant", "content": classification_json()},
            {"role": "assistant", "content": technical_plan_json()},
            {"role": "user", "content": "Second question"},
            {
                "role": "assistant",
                "content": hypothesis_json(
                    "Second question",
                    "second reply",
                    index=2,
                ),
            },
            {"role": "assistant", "content": classification_json()},
            {"role": "assistant", "content": technical_plan_json()},
        ],
        "pinned": False,
    }


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
