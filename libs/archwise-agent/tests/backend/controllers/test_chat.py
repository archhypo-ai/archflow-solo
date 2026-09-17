import json

from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import InMemorySaver

from archwise_agent import AgentService
from archwise_agent.backend import create_app
from tests.fakes import archhypo_json, fake_hypothesis_model


def test_chat_controller_returns_agent_response() -> None:
    service = AgentService(
        model=fake_hypothesis_model(["hello from the agent"]),
        checkpointer=InMemorySaver(),
    )

    with TestClient(create_app(service)) as client:
        response = client.post(
            "/api/chat",
            json={"thread_id": "curl-test", "message": "Hello"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "thread_id": "curl-test",
        "message": archhypo_json("Hello", "hello from the agent"),
        "status": "completed",
    }


def test_chat_stream_controller_emits_sse_events() -> None:
    service = AgentService(
        model=fake_hypothesis_model(["hello world"]),
        checkpointer=InMemorySaver(),
    )

    with TestClient(create_app(service)) as client:
        with client.stream(
            "POST",
            "/api/chat/stream",
            json={"thread_id": "stream-test", "message": "Hello"},
        ) as response:
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")
            lines = list(response.iter_lines())

    events = [
        line.removeprefix("event: ")
        for line in lines
        if line.startswith("event: ")
    ]
    payloads = [
        json.loads(line.removeprefix("data: "))
        for line in lines
        if line.startswith("data: ")
    ]

    assert events == ["archwise"] * len(payloads)
    assert payloads[0]["type"] == "phase"
    assert payloads[1]["type"] == "phase"
    assert payloads[-1]["type"] == "done"
    assert "".join(
        payload["text"]
        for payload in payloads
        if payload["type"] == "text_delta"
    ) == archhypo_json("Hello", "hello world")
    assert service.get_conversation("stream-test").message_count == 2


def test_chat_cancel_controller_is_idempotent_for_finished_run() -> None:
    service = AgentService(
        model=fake_hypothesis_model(["unused"]),
        checkpointer=InMemorySaver(),
    )

    with TestClient(create_app(service)) as client:
        response = client.post("/api/chat/runs/not-active/cancel")

    assert response.status_code == 200
    assert response.json() == {
        "run_id": "not-active",
        "cancelled": False,
    }


def test_chat_controller_rejects_blank_message() -> None:
    service = AgentService(
        model=fake_hypothesis_model(["unused"]),
        checkpointer=InMemorySaver(),
    )

    with TestClient(create_app(service)) as client:
        response = client.post(
            "/api/chat",
            json={"thread_id": "curl-test", "message": "   "},
        )

    assert response.status_code == 422
