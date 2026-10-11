from fastapi.testclient import TestClient

from archhypo_flow_agent.backend.app import create_app
from archhypo_flow_agent.services import AgentService


def test_chat_endpoint_saves_and_returns_conversation(tmp_path) -> None:
    service = AgentService(database_path=tmp_path / "chat.sqlite")
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
            assert response.json() == {
                "thread_id": "api-thread",
                "title": "Explore a database decision",
                "message": "Understood. Let's explore this architectural decision.",
            }

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
    finally:
        service.close()


def test_chat_endpoint_supports_portuguese_demo_reply(tmp_path) -> None:
    service = AgentService(database_path=tmp_path / "chat.sqlite")
    try:
        with TestClient(create_app(service)) as client:
            response = client.post(
                "/api/chat",
                json={
                    "thread_id": "pt-thread",
                    "message": "Avaliar decisão",
                    "language": "pt-BR",
                },
            )
    finally:
        service.close()

    assert response.status_code == 200
    assert response.json()["message"] == (
        "Entendi. Vamos explorar essa decisão arquitetural."
    )


def test_tauri_webview_origin_can_call_local_api(tmp_path) -> None:
    service = AgentService(database_path=tmp_path / "chat.sqlite")
    try:
        with TestClient(create_app(service)) as client:
            response = client.get("/health", headers={"Origin": "tauri://localhost"})
    finally:
        service.close()

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "tauri://localhost"


def test_thread_metadata_can_be_renamed_pinned_and_deleted(tmp_path) -> None:
    service = AgentService(database_path=tmp_path / "chat.sqlite")
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
    service = AgentService(database_path=tmp_path / "chat.sqlite")
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
    service = AgentService(database_path=tmp_path / "chat.sqlite")
    try:
        with TestClient(create_app(service)) as client:
            response = client.get("/api/threads/missing")
    finally:
        service.close()

    assert response.status_code == 404
