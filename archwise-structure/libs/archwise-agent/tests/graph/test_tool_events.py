from agent_stream_py import ToolResultEvent, agent_event_data
from langchain_core.messages import ToolMessage

from archwise_agent.graph.tool_events import _emit_tool_events


def test_tool_errors_are_preserved_in_stream_events() -> None:
    events: list[dict[str, object]] = []

    class Runtime:
        def stream_writer(self, event: dict[str, object]) -> None:
            events.append(event)

    _emit_tool_events(
        {
            "tools": {
                "messages": [
                    ToolMessage(
                        content="Search failed",
                        tool_call_id="search-1",
                        status="error",
                    )
                ]
            }
        },
        Runtime(),
    )

    assert events == [
        {
            "type": "tool_result",
            "tool_call_id": "search-1",
            "output": "Search failed",
            "is_error": True,
        }
    ]
    assert agent_event_data(
        ToolResultEvent(
            run_id="run-1",
            thread_id="thread-1",
            tool_call_id="search-1",
            output="Search failed",
            is_error=True,
        )
    )["is_error"] is True
