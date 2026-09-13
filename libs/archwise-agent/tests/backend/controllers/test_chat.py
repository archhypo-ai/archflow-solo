from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langgraph.checkpoint.memory import InMemorySaver

from archwise_agent import AgentService
from archwise_agent.backend import create_app


def test_chat_controller_returns_agent_response() -> None:
    service = AgentService(
        model=FakeListChatModel(responses=["hello from the agent"]),
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
        "message": "hello from the agent",
        "status": "completed",
    }


def test_chat_controller_rejects_blank_message() -> None:
    service = AgentService(
        model=FakeListChatModel(responses=["unused"]),
        checkpointer=InMemorySaver(),
    )

    with TestClient(create_app(service)) as client:
        response = client.post(
            "/api/chat",
            json={"thread_id": "curl-test", "message": "   "},
        )

    assert response.status_code == 422
