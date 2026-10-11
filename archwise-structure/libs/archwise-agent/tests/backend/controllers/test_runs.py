from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import InMemorySaver

from archwise_agent import AgentService
from archwise_agent.backend import create_app
from tests.fakes import fake_hypothesis_model


def test_active_run_endpoint_returns_null_when_thread_is_idle() -> None:
    service = AgentService(
        model=fake_hypothesis_model(["unused"]),
        checkpointer=InMemorySaver(),
    )

    with TestClient(create_app(service)) as client:
        response = client.get("/api/threads/thread-id/runs/active")

    assert response.status_code == 200
    assert response.json() is None
