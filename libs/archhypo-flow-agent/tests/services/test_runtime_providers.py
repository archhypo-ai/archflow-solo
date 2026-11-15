import importlib

import pytest
from langchain_core.messages import AIMessage
from pydantic import SecretStr

from archhypo_flow_agent.config import AgentSettings
from archhypo_flow_agent.core import ChatRequest
from archhypo_flow_agent.services import AgentService, ChatNotConfiguredError
from tests.fakes import (
    StubChatModel,
    StubSystemOneClient,
    approved_hypothesis_request,
    approved_technical_plan_request,
    stub_chat_model,
)

service_module = importlib.import_module("archhypo_flow_agent.services.agent_service")


def config(model="vendor/one", decision="vendor/decision-one", key="key-one"):
    return AgentSettings(
        _env_file=None,
        openrouter_model=model,
        system_one_model=decision,
        openrouter_api_key=SecretStr(key),
    )


def test_runtime_change_preserves_conversation_and_rotates_credentials(
    tmp_path, monkeypatch
):
    current = [config()]
    constructed = []

    def chat_factory(settings):
        constructed.append(
            (settings.openrouter_model, settings.openrouter_api_key.get_secret_value())
        )
        return StubChatModel(
            responses=[
                AIMessage(
                    content=settings.openrouter_model,
                    id=f"run-{len(constructed)}-{index}",
                )
                for index in range(20)
            ]
        )

    def decision_factory(settings):
        constructed.append(("decision", settings.system_one_model))
        return StubSystemOneClient(
            "contextual_question", "contextual_question", "contextual_question"
        )

    monkeypatch.setattr(service_module, "create_openrouter_model", chat_factory)
    monkeypatch.setattr(service_module, "create_system_one_client", decision_factory)
    service = AgentService(
        database_path=tmp_path / "runtime.sqlite",
        tools=[],
        provider_settings_resolver=lambda: current[0],
    )
    try:
        assert (
            service.respond(ChatRequest(thread_id="thread", message="one")).message
            == "vendor/one"
        )
        assert (
            service.respond(ChatRequest(thread_id="thread", message="two")).message
            == "vendor/one"
        )
        assert len(constructed) == 2
        current[0] = config("vendor/two", "vendor/decision-two", "key-two")
        assert (
            service.respond(ChatRequest(thread_id="thread", message="three")).message
            == "vendor/two"
        )
        assert constructed[-2:] == [
            ("decision", "vendor/decision-two"),
            ("vendor/two", "key-two"),
        ]
        conversation = service.get_conversation("thread")
        assert conversation is not None
        assert [m.content for m in conversation.messages] == [
            "one",
            "vendor/one",
            "two",
            "vendor/one",
            "three",
            "vendor/two",
        ]
        current[0] = config("vendor/two", "vendor/decision-two", "key-three")
        assert (
            service.respond(ChatRequest(thread_id="thread", message="four")).message
            == "vendor/two"
        )
        assert constructed[-1] == ("vendor/two", "key-three")
        current[0] = config(key="")
        with pytest.raises(ChatNotConfiguredError):
            service.respond(ChatRequest(thread_id="thread", message="not saved"))
        assert all(
            m.content != "not saved"
            for m in service.get_conversation("thread").messages
        )
    finally:
        service.close()


def test_runtime_change_resumes_pending_review(tmp_path, monkeypatch):
    current = [config()]
    monkeypatch.setattr(
        service_module,
        "create_openrouter_model",
        lambda settings: stub_chat_model(settings.openrouter_model),
    )
    monkeypatch.setattr(
        service_module,
        "create_system_one_client",
        lambda settings: StubSystemOneClient("new_uncertainty"),
    )
    service = AgentService(
        database_path=tmp_path / "review.sqlite",
        tools=[],
        provider_settings_resolver=lambda: current[0],
    )
    try:
        first = service.respond(
            ChatRequest(thread_id="review", message="Will it scale?")
        )
        assert first.pending_hypothesis_review is not None
        current[0] = config("vendor/two", "vendor/decision-two", "key-two")
        second = service.respond(approved_hypothesis_request("review"))
        assert second.pending_technical_plan_review is not None
        final = service.respond(approved_technical_plan_request("review"))
        assert final.message == "vendor/two"
        assert service.get_conversation("review").pending_hypothesis_review is None
    finally:
        service.close()
