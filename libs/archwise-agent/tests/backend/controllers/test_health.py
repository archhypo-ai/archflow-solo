from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import InMemorySaver

from archwise_agent import AgentService
from archwise_agent.backend import create_app
from archwise_agent.config import PACKAGE_VERSION
from tests.fakes import fake_hypothesis_model


def test_health_controller_reports_ready_agent() -> None:
    service = AgentService(
        model=fake_hypothesis_model(["unused"]),
        checkpointer=InMemorySaver(),
    )

    with TestClient(create_app(service)) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "agent_ready": True,
        "api_version": PACKAGE_VERSION,
        "sse_chat": True,
    }
