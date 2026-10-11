"""Stream nested agent tool calls as transport-neutral events."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from typing import Any

from langchain_core.messages import AIMessage, ToolMessage

from .support import raise_if_cancelled


def stream_agent_with_tool_events(
    agent: Any,
    input: Any,
    *,
    config: Any = None,
    context: Any = None,
    runtime: Any = None,
    on_update: Callable[[Any], bool] | None = None,
) -> Any:
    """Run an agent while forwarding tool messages through the parent runtime.

    The event payload intentionally has no transport fields. The application
    service adds the run and thread identity before serializing it as SSE.
    """

    if not hasattr(agent, "stream"):
        return agent.invoke(input, config, context=context)

    stream = _agent_stream(agent, input, config=config, context=context)
    last_update: Any = None
    structured_response: Any = None
    captured_messages: list[Any] = []
    captured_message_keys: set[object] = set()

    for update in stream:
        if on_update is not None and not on_update(update):
            return {
                "stopped": True,
                "messages": captured_messages,
            }
        last_update = update
        raise_if_cancelled(runtime)
        _capture_messages(update, captured_messages, captured_message_keys)
        _emit_tool_events(update, runtime)
        candidate = _structured_response(update)
        if candidate is not None:
            structured_response = candidate

    if structured_response is not None:
        return {"structured_response": structured_response}
    if last_update is not None:
        return last_update
    return {}


def _agent_stream(
    agent: Any,
    input: Any,
    *,
    config: Any,
    context: Any,
) -> Iterator[Any]:
    kwargs: dict[str, Any] = {"stream_mode": "updates"}
    if context is not None:
        kwargs["context"] = context

    try:
        yield from agent.stream(input, config, **kwargs)
    except TypeError as error:
        if "unexpected keyword argument" not in str(error):
            raise
        # Lightweight Runnable test doubles do not necessarily accept the
        # LangGraph stream_mode/context keywords.
        kwargs.pop("stream_mode", None)
        yield from agent.stream(input, config, **kwargs)


def _structured_response(update: Any) -> Any:
    for value in _update_values(update):
        if "structured_response" in value and value["structured_response"] is not None:
            return value["structured_response"]
    return None


def _capture_messages(
    update: Any,
    captured_messages: list[Any],
    captured_message_keys: set[object],
) -> None:
    for value in _update_values(update):
        messages = value.get("messages")
        if not isinstance(messages, list):
            continue
        for message in messages:
            message_id = getattr(message, "id", None)
            key = message_id if isinstance(message_id, str) else id(message)
            if key in captured_message_keys:
                continue
            captured_message_keys.add(key)
            captured_messages.append(message)


def _emit_tool_events(update: Any, runtime: Any) -> None:
    for value in _update_values(update):
        messages = value.get("messages")
        if not isinstance(messages, list):
            continue
        for message in messages:
            if isinstance(message, AIMessage):
                for call in message.tool_calls:
                    tool_call_id = call.get("id")
                    name = call.get("name")
                    if not isinstance(tool_call_id, str) or not isinstance(
                        name, str
                    ):
                        continue
                    _write(
                        runtime,
                        {
                            "type": "tool_call_start",
                            "tool_call_id": tool_call_id,
                            "name": name,
                        },
                    )
                    _write(
                        runtime,
                        {
                            "type": "tool_call_delta",
                            "tool_call_id": tool_call_id,
                            "text": json.dumps(
                                call.get("args", {}),
                                ensure_ascii=False,
                                default=str,
                            ),
                        },
                    )
            elif isinstance(message, ToolMessage):
                tool_call_id = message.tool_call_id
                if not isinstance(tool_call_id, str):
                    continue
                output: Any = message.content
                if isinstance(output, str):
                    try:
                        output = json.loads(output)
                    except json.JSONDecodeError:
                        pass
                _write(
                    runtime,
                    {
                        "type": "tool_result",
                        "tool_call_id": tool_call_id,
                        "output": output,
                        "is_error": getattr(message, "status", "success") == "error",
                    },
                )


def _update_values(update: Any) -> Iterator[dict[str, Any]]:
    if not isinstance(update, dict):
        return
    yield update
    for value in update.values():
        if isinstance(value, dict):
            yield value


def _write(runtime: Any, event: dict[str, Any]) -> None:
    if runtime is None:
        return
    writer = getattr(runtime, "stream_writer", None)
    if callable(writer):
        writer(event)


__all__ = ["stream_agent_with_tool_events"]
