from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langgraph.checkpoint.memory import InMemorySaver

from archwise_agent import AgentService
from archwise_agent.backend import create_app


def test_threads_controller_lists_and_loads_conversations() -> None:
    service = AgentService(
        model=FakeListChatModel(responses=["first reply", "second reply"]),
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
        }
    ]
    assert detail.status_code == 200
    assert detail.json() == {
        "thread_id": "thread-a",
        "title": "First question",
        "message_count": 4,
        "messages": [
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "first reply"},
            {"role": "user", "content": "Second question"},
            {"role": "assistant", "content": "second reply"},
        ],
    }


def test_threads_controller_returns_not_found_for_unknown_thread() -> None:
    service = AgentService(
        model=FakeListChatModel(responses=["unused"]),
        checkpointer=InMemorySaver(),
    )

    with TestClient(create_app(service)) as client:
        response = client.get("/api/threads/unknown")

    assert response.status_code == 404
