import importlib

import pytest
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from pydantic import PrivateAttr, SecretStr

from archhypo_flow_agent.config import settings
from archhypo_flow_agent.core import ChatRequest
from archhypo_flow_agent.services import AgentService
from tests.fakes import StructuredOutputStub, stub_chat_model

tavily_module = importlib.import_module("archhypo_flow_agent.tools.search.tavily")


class ToolCallingModel(StructuredOutputStub, FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        assert any(tool.name == "tavily_search" for tool in tools)
        return self


class FailingChatModel(StructuredOutputStub, FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        raise RuntimeError("model unavailable")


class ContextRecordingModel(StructuredOutputStub, FakeMessagesListChatModel):
    _system_prompts: list[str] = PrivateAttr(default_factory=list)

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self._system_prompts.append(
            "\n".join(
                str(message.content) for message in messages if message.type == "system"
            )
        )
        return super()._generate(
            messages,
            stop=stop,
            run_manager=run_manager,
            **kwargs,
        )


def test_stream_persists_and_announces_user_message_before_generation(tmp_path) -> None:
    database_path = tmp_path / "early-message.sqlite"
    service = AgentService(model=stub_chat_model(), database_path=database_path)
    history_reader = AgentService(database_path=database_path)
    stream = service.stream(
        ChatRequest(thread_id="early-thread", message="Persist immediately")
    )
    try:
        event = next(stream)
        saved_conversation = history_reader.get_conversation("early-thread")
        remaining_events = list(stream)
    finally:
        history_reader.close()
        service.close()

    assert event["type"] == "conversation_started"
    assert event["title"] == "Persist immediately"
    assert saved_conversation is not None
    assert saved_conversation.message_count == 1
    assert [message.content for message in saved_conversation.messages] == [
        "Persist immediately"
    ]
    assert remaining_events[-1]["type"] == "done"


def test_user_message_is_checkpointed_before_model_generation(tmp_path) -> None:
    service = AgentService(
        model=FailingChatModel(responses=[]),
        database_path=tmp_path / "failed-run.sqlite",
        tools=[],
    )
    try:
        with pytest.raises(RuntimeError, match="model unavailable"):
            service.respond(ChatRequest(thread_id="failed-thread", message="Save me"))
        conversation = service.get_conversation("failed-thread")
        summary = service.list_conversations()[0]
    finally:
        service.close()

    assert conversation is not None
    assert summary.message_count == 1
    assert [message.content for message in conversation.messages] == ["Save me"]


def test_run_context_isolated_by_conversation_and_refreshed_per_turn(tmp_path) -> None:
    model = ContextRecordingModel(
        responses=[AIMessage(content="Understood") for _ in range(10)]
    )
    service = AgentService(
        model=model,
        database_path=tmp_path / "context.sqlite",
        tools=[],
    )
    try:
        service.create_project(
            project_id="project-alpha",
            name="Alpha",
            icon="folder",
            color="blue",
            instructions="PROJECT_CONTEXT_ALPHA",
        )
        service.create_project(
            project_id="project-beta",
            name="Beta",
            icon="folder",
            color="green",
            instructions="PROJECT_CONTEXT_BETA",
        )

        service.respond(
            ChatRequest(
                thread_id="alpha-thread",
                message="First turn",
                project_id="project-alpha",
                global_context="GLOBAL_CONTEXT_ALPHA",
            )
        )
        service.respond(
            ChatRequest(
                thread_id="beta-thread",
                message="First turn",
                project_id="project-beta",
                global_context="GLOBAL_CONTEXT_ALPHA",
            )
        )
        service.respond(
            ChatRequest(
                thread_id="loose-thread",
                message="First turn",
                global_context="GLOBAL_CONTEXT_ALPHA",
            )
        )

        service.update_project_settings(
            "project-alpha",
            name="Alpha",
            icon="folder",
            color="blue",
            instructions="PROJECT_CONTEXT_UPDATED",
        )
        streamed_events = list(
            service.stream(
                ChatRequest(
                    thread_id="alpha-thread",
                    message="Follow up",
                    global_context="GLOBAL_CONTEXT_UPDATED",
                )
            )
        )
    finally:
        service.close()

    alpha_prompt, beta_prompt, loose_prompt, updated_prompt = model._system_prompts
    assert streamed_events[-1]["type"] == "done"
    assert "GLOBAL_CONTEXT_ALPHA" in alpha_prompt
    assert "PROJECT_CONTEXT_ALPHA" in alpha_prompt
    assert "PROJECT_CONTEXT_BETA" not in alpha_prompt
    assert "GLOBAL_CONTEXT_ALPHA" in beta_prompt
    assert "PROJECT_CONTEXT_BETA" in beta_prompt
    assert "PROJECT_CONTEXT_ALPHA" not in beta_prompt
    assert "GLOBAL_CONTEXT_ALPHA" in loose_prompt
    assert "PROJECT_CONTEXT_" not in loose_prompt
    assert "GLOBAL_CONTEXT_UPDATED" in updated_prompt
    assert "PROJECT_CONTEXT_UPDATED" in updated_prompt
    assert "GLOBAL_CONTEXT_ALPHA" not in updated_prompt
    assert "PROJECT_CONTEXT_ALPHA" not in updated_prompt


def test_configured_tavily_calls_are_returned_and_restored(
    monkeypatch, tmp_path
) -> None:
    class FakeTavilyClient:
        def search(self, **kwargs):
            assert kwargs["query"] == "Python release notes"
            return {
                "answer": "The release notes are published.",
                "results": [
                    {
                        "title": "Python release notes",
                        "url": "https://python.org/downloads/release/",
                        "content": "Official release information.",
                        "score": 0.9,
                    }
                ],
            }

    monkeypatch.setattr(settings, "tavily_api_key", SecretStr("test-key"))
    monkeypatch.setattr(
        tavily_module,
        "_tavily_client",
        lambda _: FakeTavilyClient(),
    )
    model = ToolCallingModel(
        responses=[
            AIMessage(
                content="Vou pesquisar notícias recentes sobre esse título.",
                tool_calls=[
                    {
                        "name": "tavily_search",
                        "args": {"query": "Python release notes"},
                        "id": "lookup-1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="Python release notes are available."),
            AIMessage(content="You're welcome."),
        ]
    )
    service = AgentService(model=model, database_path=tmp_path / "tool-calls.sqlite")

    try:
        response = service.respond(
            ChatRequest(thread_id="tool-thread", message="Find Python release notes")
        )
        follow_up = service.respond(
            ChatRequest(thread_id="tool-thread", message="Thanks")
        )
        conversation = service.get_conversation("tool-thread")
    finally:
        service.close()

    assert response.message == "Python release notes are available."
    assert [call.model_dump() for call in response.tool_calls] == [
        {
            "id": "lookup-1",
            "name": "tavily_search",
            "args": {"query": "Python release notes"},
            "result": {
                "status": "ok",
                "query": "Python release notes",
                "answer": "The release notes are published.",
                "results": [
                    {
                        "title": "Python release notes",
                        "url": "https://python.org/downloads/release/",
                        "content": "Official release information.",
                        "score": 0.9,
                        "published_date": None,
                    }
                ],
            },
            "is_error": False,
        }
    ]
    assert follow_up.tool_calls == []
    assert conversation is not None
    assert conversation.messages[-3].tool_calls == response.tool_calls
    assert conversation.messages[-1].tool_calls == []
    assert [message.content for message in conversation.messages] == [
        "Find Python release notes",
        "Python release notes are available.",
        "Thanks",
        "You're welcome.",
    ]


def test_stream_emits_tool_calls_and_results_before_the_final_reply(
    monkeypatch, tmp_path
) -> None:
    class FakeTavilyClient:
        def search(self, **kwargs):
            return {
                "answer": f"Found {kwargs['query']}.",
                "results": [],
            }

    monkeypatch.setattr(settings, "tavily_api_key", SecretStr("test-key"))
    monkeypatch.setattr(
        tavily_module,
        "_tavily_client",
        lambda _: FakeTavilyClient(),
    )
    model = ToolCallingModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "tavily_search",
                        "args": {"query": "first query"},
                        "id": "lookup-1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "tavily_search",
                        "args": {"query": "second query"},
                        "id": "lookup-2",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="Here is the final answer."),
            AIMessage(content="The first turn is summarized."),
        ]
    )
    service = AgentService(model=model, database_path=tmp_path / "stream.sqlite")

    try:
        events = list(
            service.stream(
                ChatRequest(thread_id="stream-thread", message="Research both topics")
            )
        )
        follow_up_events = list(
            service.stream(
                ChatRequest(thread_id="stream-thread", message="Summarize that")
            )
        )
    finally:
        service.close()

    event_types = [event["type"] for event in events]
    assert all(event["protocol_version"] == 1 for event in events)
    assert all(event["thread_id"] == "stream-thread" for event in events)
    assert len({event["run_id"] for event in events}) == 1
    assert events[0]["run_id"] != follow_up_events[0]["run_id"]
    assert event_types.count("tool_call_start") == 2
    assert event_types.count("tool_result") == 2
    first_call = next(
        index
        for index, event in enumerate(events)
        if event.get("tool_call_id") == "lookup-1"
        and event["type"] == "tool_call_start"
    )
    first_result = next(
        index
        for index, event in enumerate(events)
        if event.get("tool_call_id") == "lookup-1" and event["type"] == "tool_result"
    )
    second_call = next(
        index
        for index, event in enumerate(events)
        if event.get("tool_call_id") == "lookup-2"
        and event["type"] == "tool_call_start"
    )
    second_result = next(
        index
        for index, event in enumerate(events)
        if event.get("tool_call_id") == "lookup-2" and event["type"] == "tool_result"
    )
    final_reply = next(
        index for index, event in enumerate(events) if event["type"] == "text_delta"
    )
    assert first_call < first_result < second_call < second_result < final_reply
    assert events[final_reply]["text"] == "Here is the final answer."
    assert events[-1]["type"] == "done"
    assert not any(
        event["type"] in {"tool_call_start", "tool_call_delta", "tool_result"}
        for event in follow_up_events
    )
    assert follow_up_events[-2]["text"] == "The first turn is summarized."
