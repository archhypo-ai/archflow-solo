import json

from fastapi.testclient import TestClient

from archhypo_flow_agent.backend.app import create_app
from archhypo_flow_agent.services import AgentService
from tests.fakes import stub_chat_model


def test_chat_endpoint_saves_and_returns_conversation(tmp_path) -> None:
    service = AgentService(
        model=stub_chat_model(), database_path=tmp_path / "chat.sqlite"
    )
    app = create_app(service)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/chat",
                json={
                    "thread_id": "api-thread",
                    "message": "Explore a database decision",
                    "language": "en",
                },
            )

            assert response.status_code == 200
            assert response.json()["thread_id"] == "api-thread"
            assert response.json()["pending_hypothesis_review"]["statement"]
            assert "Review the proposed hypothesis" in response.json()["message"]

            approved = client.post(
                "/api/chat",
                json={
                    "thread_id": "api-thread",
                    "message": "",
                    "language": "en",
                    "hypothesis_review": {"decision": "approved"},
                },
            )
            assert approved.status_code == 200
            assert approved.json()["pending_hypothesis_review"] is None
            assert approved.json()["pending_technical_plan_review"]["kind"] == (
                "technical_plan_review"
            )
            assert "technical plan" in approved.json()["message"]

            finalized = client.post(
                "/api/chat",
                json={
                    "thread_id": "api-thread",
                    "message": "",
                    "language": "en",
                    "technical_plan_review": {"decision": "approved"},
                },
            )
            assert finalized.status_code == 200
            assert finalized.json()["message"] == (
                "Understood. Let's explore this architectural decision."
            )
            assert finalized.json()["pending_technical_plan_review"] is None

            listed = client.get("/api/threads")
            assert listed.status_code == 200
            assert listed.json()[0]["thread_id"] == "api-thread"
            assert listed.json()[0]["message_count"] == 2

            loaded = client.get("/api/threads/api-thread")
            assert loaded.status_code == 200
            assert [message["role"] for message in loaded.json()["messages"]] == [
                "user",
                "assistant",
            ]
            assert loaded.json()["pending_hypothesis_review"] is None
            assert loaded.json()["pending_technical_plan_review"] is None
            completed_kinds = [
                review["kind"] for review in loaded.json()["completed_reviews"]
            ]
            assert completed_kinds == [
                "hypothesis_review",
                "technical_plan_review",
            ]
            assert [
                review["after_message_count"]
                for review in loaded.json()["completed_reviews"]
            ] == [1, 1]
    finally:
        service.close()


def test_chat_requires_an_explicitly_configured_model(tmp_path) -> None:
    service = AgentService(database_path=tmp_path / "unconfigured.sqlite")
    try:
        with TestClient(create_app(service)) as client:
            health = client.get("/health")
            response = client.post(
                "/api/chat",
                json={"thread_id": "offline-thread", "message": "Hello"},
            )
    finally:
        service.close()

    assert health.json()["agent_ready"] is False
    assert response.status_code == 503
    assert "OPENROUTER_API_KEY" in response.json()["detail"]


def test_chat_stream_pauses_and_resumes_the_hypothesis_review(tmp_path) -> None:
    service = AgentService(
        model=stub_chat_model(), database_path=tmp_path / "stream.sqlite"
    )
    try:
        with TestClient(create_app(service)) as client:
            pending_events = _stream_events(
                client,
                {
                    "thread_id": "stream-thread",
                    "message": "Explore a database decision",
                    "language": "en",
                },
            )
            assert [event["type"] for event in pending_events] == [
                "conversation_started",
                "phase",
                "interrupt",
            ]
            assert pending_events[0]["user_message"] == "Explore a database decision"
            assert pending_events[0]["project_id"] is None
            assert pending_events[-1]["payload"]["kind"] == "hypothesis_review"
            assert pending_events[-1]["payload"]["hypothesis"]["statement"]
            assert all(event["protocol_version"] == 1 for event in pending_events)
            assert all(
                event["thread_id"] == "stream-thread" for event in pending_events
            )
            assert len({event["run_id"] for event in pending_events}) == 1
            paused_conversation = client.get("/api/threads/stream-thread")
            assert paused_conversation.json()["pending_hypothesis_review"]["kind"] == (
                "hypothesis_review"
            )
            blocked_message = client.post(
                "/api/chat",
                json={"thread_id": "stream-thread", "message": "Skip review"},
            )
            assert blocked_message.status_code == 409

            rejected_events = _stream_events(
                client,
                {
                    "thread_id": "stream-thread",
                    "message": "",
                    "language": "en",
                    "hypothesis_review": {
                        "decision": "rejected",
                        "reason": "Make it directly testable.",
                    },
                },
            )
            revised = rejected_events[-1]["payload"]["hypothesis"]
            assert rejected_events[-1]["type"] == "interrupt"
            assert rejected_events[0]["user_message"] == ""
            assert "Make it directly testable." in revised["statement"]

            plan_pending_events = _stream_events(
                client,
                {
                    "thread_id": "stream-thread",
                    "message": "",
                    "language": "en",
                    "hypothesis_review": {"decision": "approved"},
                },
            )
            assert plan_pending_events[-1]["type"] == "interrupt"
            plan_payload = plan_pending_events[-1]["payload"]
            assert plan_payload["kind"] == "technical_plan_review"
            assert plan_payload["assessment"]["impact"] == "Medium"
            assert plan_payload["assessment"]["uncertainty"] == "High"
            assert plan_payload["technical_plan"]["items"][0]["title"]
            paused_plan_conversation = client.get("/api/threads/stream-thread")
            assert paused_plan_conversation.json()["pending_technical_plan_review"][
                "kind"
            ] == "technical_plan_review"

            blocked_plan_message = client.post(
                "/api/chat",
                json={"thread_id": "stream-thread", "message": "Skip plan review"},
            )
            assert blocked_plan_message.status_code == 409
            wrong_review_decision = client.post(
                "/api/chat",
                json={
                    "thread_id": "stream-thread",
                    "message": "Approve the wrong stage.",
                    "hypothesis_review": {"decision": "approved"},
                },
            )
            assert wrong_review_decision.status_code == 409

            revised_plan_events = _stream_events(
                client,
                {
                    "thread_id": "stream-thread",
                    "message": "",
                    "language": "en",
                    "technical_plan_review": {
                        "decision": "rejected",
                        "reason": "Add a rollback action.",
                    },
                },
            )
            assert revised_plan_events[-1]["type"] == "interrupt"
            assert revised_plan_events[-1]["payload"]["kind"] == (
                "technical_plan_review"
            )
            assert "Add a rollback action." in revised_plan_events[-1]["payload"][
                "technical_plan"
            ]["items"][0]["description"]

            approved_events = _stream_events(
                client,
                {
                    "thread_id": "stream-thread",
                    "message": "",
                    "language": "en",
                    "technical_plan_review": {"decision": "approved"},
                },
            )
            assert approved_events[-1]["type"] == "done"
            assert approved_events[-1]["status"] == "completed"
            assert approved_events[-1]["title"] == "Explore a database decision"
            text_events = [
                event for event in approved_events if event["type"] == "text_delta"
            ]
            assert text_events[0]["text"] == (
                "Understood. Let's explore this architectural decision."
            )
            loaded = client.get("/api/threads/stream-thread")
            assert loaded.status_code == 200
            assert loaded.json()["pending_hypothesis_review"] is None
            assert loaded.json()["pending_technical_plan_review"] is None
            assert [message["content"] for message in loaded.json()["messages"]] == [
                "Explore a database decision",
                "Understood. Let's explore this architectural decision.",
            ]
            completed_kinds = [
                review["kind"] for review in loaded.json()["completed_reviews"]
            ]
            assert completed_kinds == [
                "hypothesis_review",
                "technical_plan_review",
            ]
    finally:
        service.close()


def test_chat_endpoint_uses_configured_model_response(tmp_path) -> None:
    service = AgentService(
        model=stub_chat_model("Resposta configurada pelo modelo."),
        database_path=tmp_path / "chat.sqlite",
    )
    try:
        with TestClient(create_app(service)) as client:
            pending = client.post(
                "/api/chat",
                json={
                    "thread_id": "pt-thread",
                    "message": "Avaliar decisão",
                    "language": "pt-BR",
                },
            )
            response = client.post(
                "/api/chat",
                json={
                    "thread_id": "pt-thread",
                    "message": "",
                    "language": "pt-BR",
                    "hypothesis_review": {"decision": "approved"},
                },
            )
            response = client.post(
                "/api/chat",
                json={
                    "thread_id": "pt-thread",
                    "message": "",
                    "language": "pt-BR",
                    "technical_plan_review": {"decision": "approved"},
                },
            )
    finally:
        service.close()

    assert response.status_code == 200
    assert response.json()["message"] == "Resposta configurada pelo modelo."
    assert pending.json()["pending_hypothesis_review"] is not None


def test_rejected_reviews_require_a_reason_in_the_api(tmp_path) -> None:
    service = AgentService(
        model=stub_chat_model(), database_path=tmp_path / "review-validation.sqlite"
    )
    try:
        with TestClient(create_app(service)) as client:
            client.post(
                "/api/chat",
                json={"thread_id": "review-thread", "message": "Review this"},
            )
            response = client.post(
                "/api/chat",
                json={
                    "thread_id": "review-thread",
                    "message": "Reject",
                    "hypothesis_review": {"decision": "rejected"},
                },
            )
            assert response.status_code == 422
            client.post(
                "/api/chat",
                json={
                    "thread_id": "review-thread",
                    "message": "",
                    "hypothesis_review": {"decision": "approved"},
                },
            )
            plan_response = client.post(
                "/api/chat",
                json={
                    "thread_id": "review-thread",
                    "message": "",
                    "technical_plan_review": {"decision": "rejected"},
                },
            )
    finally:
        service.close()

    assert plan_response.status_code == 422


def _stream_events(client: TestClient, payload: dict[str, object]) -> list[dict]:
    with client.stream("POST", "/api/chat/stream", json=payload) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        return [
            json.loads(line.removeprefix("data: "))
            for line in response.iter_lines()
            if line.startswith("data: ")
        ]


def test_tauri_webview_origin_can_call_local_api(tmp_path) -> None:
    service = AgentService(
        model=stub_chat_model(), database_path=tmp_path / "chat.sqlite"
    )
    try:
        with TestClient(create_app(service)) as client:
            response = client.get("/health", headers={"Origin": "tauri://localhost"})
            preflight = client.options(
                "/api/projects/project-1",
                headers={
                    "Origin": "tauri://localhost",
                    "Access-Control-Request-Method": "PUT",
                    "Access-Control-Request-Headers": "content-type",
                },
            )
    finally:
        service.close()

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "tauri://localhost"
    assert preflight.status_code == 200
    assert "PUT" in preflight.headers["access-control-allow-methods"]


def test_projects_can_be_persisted_and_linked_to_conversations(tmp_path) -> None:
    service = AgentService(
        model=stub_chat_model(), database_path=tmp_path / "projects.sqlite"
    )
    try:
        with TestClient(create_app(service)) as client:
            created = client.post(
                "/api/projects",
                json={
                    "id": "project-1",
                    "name": "Architecture",
                    "icon": "folder",
                    "color": "blue",
                    "instructions": "Prefer simple designs.",
                },
            )
            assert created.status_code == 201
            assert created.json()["id"] == "project-1"
            assert client.get("/api/projects").json()[0]["name"] == "Architecture"
            renamed_project = client.patch(
                "/api/projects/project-1",
                json={"name": "Platform"},
            )
            assert renamed_project.status_code == 200
            assert renamed_project.json()["name"] == "Platform"
            settings = client.put(
                "/api/projects/project-1",
                json={
                    "name": "Platform",
                    "icon": "briefcase",
                    "color": "red",
                    "instructions": "Use the project context.",
                },
            )
            assert settings.status_code == 200
            assert settings.json()["icon"] == "briefcase"
            assert settings.json()["color"] == "red"
            assert settings.json()["instructions"] == "Use the project context."

            client.post(
                "/api/chat",
                json={"thread_id": "project-thread", "message": "Hello"},
            )
            assigned = client.patch(
                "/api/threads/project-thread/project",
                json={"project_id": "project-1"},
            )
            assert assigned.status_code == 200
            assert assigned.json()["project_id"] == "project-1"

            unassigned = client.patch(
                "/api/threads/project-thread/project",
                json={"project_id": None},
            )
            assert unassigned.status_code == 200
            assert unassigned.json()["project_id"] is None

            created_chat = client.post(
                "/api/chat",
                json={
                    "thread_id": "created-in-project",
                    "message": "Project conversation",
                    "project_id": "project-1",
                },
            )
            assert created_chat.status_code == 200
            assert client.get("/api/threads").json()[0]["project_id"] == "project-1"

            deleted = client.delete("/api/projects/project-1")
            assert deleted.status_code == 204
            assert client.get("/api/threads/created-in-project").status_code == 404
            assert client.get("/api/threads/project-thread").status_code == 200
    finally:
        service.close()


def test_thread_metadata_can_be_renamed_pinned_and_deleted(tmp_path) -> None:
    service = AgentService(
        model=stub_chat_model(), database_path=tmp_path / "chat.sqlite"
    )
    try:
        with TestClient(create_app(service)) as client:
            client.post(
                "/api/chat",
                json={
                    "thread_id": "managed-thread",
                    "message": "Explore a decision",
                    "language": "en",
                },
            )

            updated = client.patch(
                "/api/threads/managed-thread",
                json={"title": "A clearer title", "pinned": True},
            )
            assert updated.status_code == 200
            assert updated.json()["title"] == "A clearer title"
            assert updated.json()["pinned"] is True

            listed = client.get("/api/threads")
            assert listed.json()[0]["pinned"] is True

            deleted = client.delete("/api/threads/managed-thread")
            assert deleted.status_code == 204
            assert client.get("/api/threads/managed-thread").status_code == 404
            assert client.get("/api/threads").json() == []
    finally:
        service.close()


def test_thread_update_rejects_blank_titles_and_empty_updates(tmp_path) -> None:
    service = AgentService(
        model=stub_chat_model(), database_path=tmp_path / "chat.sqlite"
    )
    try:
        with TestClient(create_app(service)) as client:
            client.post(
                "/api/chat",
                json={"thread_id": "validation-thread", "message": "Hi"},
            )
            blank_title = client.patch(
                "/api/threads/validation-thread",
                json={"title": "   "},
            )
            empty_update = client.patch(
                "/api/threads/validation-thread",
                json={},
            )
    finally:
        service.close()

    assert blank_title.status_code == 422
    assert empty_update.status_code == 422


def test_unknown_thread_returns_not_found(tmp_path) -> None:
    service = AgentService(
        model=stub_chat_model(), database_path=tmp_path / "chat.sqlite"
    )
    try:
        with TestClient(create_app(service)) as client:
            response = client.get("/api/threads/missing")
    finally:
        service.close()

    assert response.status_code == 404
