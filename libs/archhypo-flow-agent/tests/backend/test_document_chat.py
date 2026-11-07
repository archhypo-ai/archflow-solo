import base64

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage

from archhypo_flow_agent.agents import documentary_research
from archhypo_flow_agent.backend.app import create_app
from archhypo_flow_agent.services import AgentService
from archhypo_flow_agent.services.chat_projection import project_messages
from tests.fakes import StubSystemOneClient, stub_chat_model


def test_legacy_attachment_without_size_remains_readable():
    messages = project_messages(
        [
            HumanMessage(
                content="Read this",
                additional_kwargs={
                    "document_attachments": [{"name": "adr.md", "text": "x"}]
                },
            )
        ]
    )
    assert messages[0].attachments == [{"name": "adr.md"}]


def test_document_request_streams_answer_and_preserves_names(tmp_path, monkeypatch):
    calls = []

    class FakeAgent:
        def invoke(self, value, config):
            calls.append(value)
            return {"messages": [AIMessage(content="ADR: documented decision.")]}

    def build(model, documents):
        assert [(item.name, item.text) for item in documents] == [("adr.md", "secret")]
        return FakeAgent()

    monkeypatch.setattr(documentary_research, "build_documentary_research_agent", build)
    router = StubSystemOneClient()
    service = AgentService(
        model=stub_chat_model(), system_one_client=router, database_path=tmp_path / "db"
    )
    with TestClient(create_app(service)) as client:
        response = client.post(
            "/api/chat/stream",
            json={
                "thread_id": "doc-thread",
                "message": "Analyze this ADR",
                "attachments": [
                    {
                        "name": "adr.md",
                        "data": base64.b64encode(b"secret").decode(),
                        "folder_id": "folder-1",
                        "folder_name": "adrs",
                    }
                ],
            },
        )
        assert "ADR: documented decision." in response.text
        assert "secret" not in response.text
        history = client.get("/api/threads/doc-thread").json()
        assert history["messages"][0]["attachments"] == [
            {
                "name": "adr.md",
                "size_bytes": 6,
                "folder_id": "folder-1",
                "folder_name": "adrs",
            }
        ]
        assert "secret" not in str(history)
        assert router.calls == 0
        assert calls
    service.close()


def test_document_request_rejects_source_code(tmp_path):
    service = AgentService(
        model=stub_chat_model(),
        system_one_client=StubSystemOneClient(),
        database_path=tmp_path / "db",
    )
    with TestClient(create_app(service)) as client:
        response = client.post(
            "/api/chat",
            json={
                "thread_id": "doc-thread",
                "message": "Analyze",
                "attachments": [
                    {"name": "main.py", "data": base64.b64encode(b"code").decode()}
                ],
            },
        )
        assert response.status_code == 422
        assert "Unsupported" in response.text
    service.close()
