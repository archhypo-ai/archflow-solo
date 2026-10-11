import importlib

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from pydantic import SecretStr

from archhypo_flow_agent.config import settings
from archhypo_flow_agent.core import ChatRequest
from archhypo_flow_agent.services import AgentService

tavily_module = importlib.import_module(
    "archhypo_flow_agent.tools.search.tavily"
)


class ToolCallingModel(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        assert any(tool.name == "tavily_search" for tool in tools)
        return self


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
        if event.get("tool_call_id") == "lookup-1"
        and event["type"] == "tool_result"
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
        if event.get("tool_call_id") == "lookup-2"
        and event["type"] == "tool_result"
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
