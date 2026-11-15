import importlib
import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from archhypo_flow_agent.backend.app import create_app
from archhypo_flow_agent.config import AgentSettings, settings
from archhypo_flow_agent.core import StructuredOutputError
from archhypo_flow_agent.providers import SystemOneRequestError, SystemOneResponseError
from archhypo_flow_agent.services import AgentService
from tests.fakes import StubSystemOneClient, stub_chat_model


def test_chat_endpoint_saves_and_returns_conversation(tmp_path) -> None:
    database_path = tmp_path / "chat.sqlite"
    service = AgentService(
        model=stub_chat_model(),
        system_one_client=StubSystemOneClient(),
        database_path=database_path,
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

    with sqlite3.connect(database_path) as connection:
        artifact = connection.execute(
            """SELECT status, outcome, thread_id, hitl_enabled, result_json
               FROM archhypo_artifacts"""
        ).fetchone()
    assert artifact is not None
    assert artifact[:4] == ("open", "not_evaluated", "api-thread", 1)
    assert json.loads(artifact[4])["hypothesis"]["statement"]


@pytest.mark.parametrize("path", ["/api/chat", "/api/chat/stream"])
@pytest.mark.parametrize(
    ("env_enabled", "request_enabled"),
    [(False, None), (False, True), (False, False), (True, False)],
)
def test_disabled_hitl_finishes_without_review_cards(
    monkeypatch, tmp_path, path, env_enabled, request_enabled
) -> None:
    monkeypatch.setattr(settings, "hitl_enabled", env_enabled)
    database_path = tmp_path / "without-hitl.sqlite"
    service = AgentService(
        model=stub_chat_model(),
        system_one_client=StubSystemOneClient(),
        database_path=database_path,
        tools=[],
    )
    expected_message = "Understood. Let's explore this architectural decision."
    try:
        with TestClient(create_app(service)) as client:
            payload = {"thread_id": "without-hitl", "message": "Assess peak capacity."}
            if request_enabled is not None:
                payload["hitl_enabled"] = request_enabled
            if path == "/api/chat":
                response = client.post(path, json=payload)
                assert response.status_code == 200
                assert response.json()["message"] == expected_message
                assert response.json()["pending_hypothesis_review"] is None
                assert response.json()["pending_technical_plan_review"] is None
            else:
                events = _stream_events(client, payload)
                assert events[-1]["type"] == "done"
                assert events[-1]["status"] == "completed"
                assert events[-1]["message"] == expected_message
                assert not any(event["type"] == "interrupt" for event in events)

            conversation = client.get("/api/threads/without-hitl").json()
            assert conversation["pending_hypothesis_review"] is None
            assert conversation["pending_technical_plan_review"] is None
            assert conversation["completed_reviews"] == []
            assert [message["role"] for message in conversation["messages"]] == [
                "user", "assistant"
            ]
    finally:
        service.close()

    with sqlite3.connect(database_path) as connection:
        artifact = connection.execute(
            "SELECT hitl_enabled, result_json FROM archhypo_artifacts"
        ).fetchone()
    assert artifact is not None
    assert artifact[0] == 0
    assert json.loads(artifact[1])["technical_plan"]["items"]

    history_service = AgentService(database_path=database_path)
    try:
        restored = history_service.get_conversation("without-hitl")
        assert restored is not None
        assert restored.messages[-1].content == expected_message
        assert restored.pending_hypothesis_review is None
        assert restored.pending_technical_plan_review is None
        assert restored.completed_reviews == []
    finally:
        history_service.close()


def test_hitl_preference_is_resolved_for_each_request(tmp_path) -> None:
    service = AgentService(
        model=stub_chat_model(),
        system_one_client=StubSystemOneClient(),
        database_path=tmp_path / "hitl-preference.sqlite",
        tools=[],
    )
    try:
        with TestClient(create_app(service)) as client:
            payload = {"thread_id": "toggle-hitl", "message": "Assess peak capacity."}
            disabled = client.post("/api/chat", json={**payload, "hitl_enabled": False})
            assert disabled.status_code == 200
            assert disabled.json()["pending_hypothesis_review"] is None
            assert disabled.json()["pending_technical_plan_review"] is None
            assert client.get("/api/threads/toggle-hitl").json()[
                "completed_reviews"
            ] == []

            enabled = client.post("/api/chat", json={**payload, "hitl_enabled": True})
            assert enabled.status_code == 200
            assert enabled.json()["pending_hypothesis_review"] is not None
            plan = client.post(
                "/api/chat",
                json={
                    "thread_id": "toggle-hitl",
                    "hitl_enabled": True,
                    "hypothesis_review": {"decision": "approved"},
                },
            )
            assert plan.status_code == 200
            assert plan.json()["pending_technical_plan_review"] is not None
            completed = client.post(
                "/api/chat",
                json={
                    "thread_id": "toggle-hitl",
                    "hitl_enabled": True,
                    "technical_plan_review": {"decision": "approved"},
                },
            )
            assert completed.status_code == 200

            disabled_again = _stream_events(
                client, {**payload, "hitl_enabled": False}
            )
            assert disabled_again[-1]["type"] == "done"
            assert not any(event["type"] == "interrupt" for event in disabled_again)
            conversation = client.get("/api/threads/toggle-hitl").json()
            assert conversation["pending_hypothesis_review"] is None
            assert conversation["pending_technical_plan_review"] is None
            assert [review["kind"] for review in conversation["completed_reviews"]] == [
                "hypothesis_review", "technical_plan_review"
            ]
    finally:
        service.close()


@pytest.mark.parametrize("value", [None, "invalid", {}])
def test_chat_rejects_invalid_hitl_preferences(tmp_path, value) -> None:
    service = AgentService(database_path=tmp_path / "invalid-hitl.sqlite")
    try:
        with TestClient(create_app(service)) as client:
            response = client.post(
                "/api/chat",
                json={
                    "thread_id": "invalid-hitl",
                    "message": "Hello",
                    "hitl_enabled": value,
                },
            )
            assert response.status_code == 422
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


@pytest.mark.parametrize("model_name", [None, "", "   "])
def test_missing_system_one_configuration_keeps_history_available(
    monkeypatch, tmp_path, model_name
) -> None:
    app_module = importlib.import_module("archhypo_flow_agent.backend.app")
    configuration = AgentSettings(
        _env_file=None,
        openrouter_api_key="test-key",
        system_one_model=model_name,
    )
    monkeypatch.setattr(
        app_module, "effective_provider_settings", lambda: configuration
    )
    monkeypatch.setattr(
        app_module,
        "AgentService",
        lambda **kwargs: AgentService(
            database_path=tmp_path / "history-only.sqlite", **kwargs
        ),
    )

    with TestClient(create_app()) as client:
        health = client.get("/health")
        assert health.json()["agent_ready"] is False
        assert "SYSTEM_ONE_MODEL" in health.json()["configuration_error"]
        assert client.get("/api/threads").status_code == 200
        for path in ("/api/chat", "/api/chat/stream"):
            response = client.post(
                path,
                json={"thread_id": "unconfigured-router", "message": "Hello"},
            )
            assert response.status_code == 503
            assert "SYSTEM_ONE_MODEL" in response.json()["detail"]


@pytest.mark.parametrize("error_type", [SystemOneRequestError, SystemOneResponseError])
def test_routing_failures_are_explicit_in_chat_and_stream(tmp_path, error_type) -> None:
    system_one = StubSystemOneClient(error=error_type("private provider details"))
    service = AgentService(
        model=stub_chat_model(),
        system_one_client=system_one,
        database_path=tmp_path / "failed-router.sqlite",
    )
    try:
        with TestClient(create_app(service)) as client:
            response = client.post(
                "/api/chat",
                json={"thread_id": "failed-router", "message": "Explain ArchHypo"},
            )
            assert response.status_code == 502
            assert "SystemOne request routing failed" in response.json()["detail"]
            assert "private provider details" not in response.json()["detail"]

            events = _stream_events(
                client,
                {"thread_id": "failed-stream", "message": "Gere outra hipótese"},
            )
            assert [event["type"] for event in events] == [
                "conversation_started", "phase", "error"
            ]
            assert "SystemOne request routing failed" in events[-1]["message"]
            assert "private provider details" not in events[-1]["message"]
            assert system_one.calls == 2
            for thread_id in ("failed-router", "failed-stream"):
                history = client.get(f"/api/threads/{thread_id}").json()
                assert len(history["messages"]) == 1
                assert history["messages"][0]["role"] == "user"
                assert history["pending_hypothesis_review"] is None
    finally:
        service.close()


def test_assessment_schema_failure_is_reported_separately_from_openrouter(
    monkeypatch, tmp_path
) -> None:
    service = AgentService(
        model=stub_chat_model(),
        system_one_client=StubSystemOneClient(),
        database_path=tmp_path / "assessment-schema-error.sqlite",
    )

    def fail_respond(_request):
        raise StructuredOutputError(stage="hypothesis_assessment", attempts=2)

    def fail_stream(_request, *, run_id=None):
        def events():
            raise StructuredOutputError(stage="hypothesis_assessment", attempts=2)
            yield {}

        return events()

    monkeypatch.setattr(service, "respond", fail_respond)
    monkeypatch.setattr(service, "stream", fail_stream)
    expected_detail = (
        "The model returned an incomplete assessment after one correction attempt."
    )
    try:
        with TestClient(create_app(service)) as client:
            response = client.post(
                "/api/chat",
                json={"thread_id": "assessment-error", "message": "Assess this"},
            )
            events = _stream_events(
                client,
                {"thread_id": "assessment-error", "message": "Assess this"},
            )
    finally:
        service.close()

    assert response.status_code == 502
    assert expected_detail in response.json()["detail"]
    assert "OpenRouter request failed" not in response.json()["detail"]
    assert events[-1]["type"] == "error"
    assert expected_detail in events[-1]["message"]


def test_chat_stream_pauses_and_resumes_the_hypothesis_review(tmp_path) -> None:
    service = AgentService(
        model=stub_chat_model(),
        system_one_client=StubSystemOneClient(),
        database_path=tmp_path / "stream.sqlite",
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
        system_one_client=StubSystemOneClient(),
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
        model=stub_chat_model(),
        system_one_client=StubSystemOneClient(),
        database_path=tmp_path / "review-validation.sqlite",
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
        model=stub_chat_model(),
        system_one_client=StubSystemOneClient(),
        database_path=tmp_path / "chat.sqlite",
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
        model=stub_chat_model(),
        system_one_client=StubSystemOneClient(),
        database_path=tmp_path / "projects.sqlite",
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
        model=stub_chat_model(),
        system_one_client=StubSystemOneClient(),
        database_path=tmp_path / "chat.sqlite",
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
        model=stub_chat_model(),
        system_one_client=StubSystemOneClient(),
        database_path=tmp_path / "chat.sqlite",
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
        model=stub_chat_model(),
        system_one_client=StubSystemOneClient(),
        database_path=tmp_path / "chat.sqlite",
    )
    try:
        with TestClient(create_app(service)) as client:
            response = client.get("/api/threads/missing")
    finally:
        service.close()

    assert response.status_code == 404
