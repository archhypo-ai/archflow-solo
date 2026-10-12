"""Projection helpers for LangGraph messages and chat stream events."""

import json
from collections.abc import Iterator, Sequence

from langchain_core.messages import BaseMessage

from archhypo_flow_agent.core import ToolCallRecord

from .contracts import ConversationMessage


def stream_event_data(
    run_id: str,
    thread_id: str,
    event_type: str,
    **fields: object,
) -> dict[str, object]:
    return {
        "protocol_version": 1,
        "run_id": run_id,
        "thread_id": thread_id,
        "type": event_type,
        **fields,
    }


def messages_from_update(update: object) -> Iterator[BaseMessage]:
    if not isinstance(update, dict):
        return

    values = list(update.values())
    while values:
        value = values.pop()
        if not isinstance(value, dict):
            continue
        messages = value.get("messages")
        if isinstance(messages, list):
            yield from (
                message for message in messages if isinstance(message, BaseMessage)
            )
        values.extend(child for child in value.values() if isinstance(child, dict))


def tool_calls_from_messages(
    messages: Sequence[BaseMessage],
) -> list[ToolCallRecord]:
    calls: list[dict[str, object]] = []
    calls_by_id: dict[str, dict[str, object]] = {}

    for message in messages:
        if message.type == "ai":
            for index, call in enumerate(getattr(message, "tool_calls", [])):
                call_id = str(call.get("id") or f"tool-call-{index}")
                args = call.get("args")
                record: dict[str, object] = {
                    "id": call_id,
                    "name": str(call.get("name") or "unknown_tool"),
                    "args": args if isinstance(args, dict) else {},
                    "result": None,
                    "is_error": False,
                }
                calls.append(record)
                calls_by_id[call_id] = record
        elif message.type == "tool":
            call_id = str(getattr(message, "tool_call_id", ""))
            record = calls_by_id.get(call_id)
            if record is not None:
                record["result"] = tool_result_value(message.content)
                record["is_error"] = getattr(message, "status", "success") == "error"

    return [ToolCallRecord(**call) for call in calls]


def tool_result_value(content: object) -> object:
    if not isinstance(content, str):
        return content
    try:
        decoded = json.loads(content)
    except ValueError:
        return content
    return decoded if isinstance(decoded, (dict, list)) else content


def message_text(message: BaseMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    return "".join(
        str(block["text"])
        for block in content
        if isinstance(block, dict) and isinstance(block.get("text"), str)
    )


def project_messages(messages: Sequence[BaseMessage]) -> list[ConversationMessage]:
    """Project checkpoint messages into the user-visible transcript."""

    projected: list[ConversationMessage] = []
    turn_messages: list[BaseMessage] = []
    for message in messages:
        if message.type == "human":
            turn_messages = []
            projected.append(
                ConversationMessage(role="user", content=message_text(message))
            )
            continue

        if message.type not in {"ai", "tool"}:
            continue
        turn_messages.append(message)
        text = message_text(message)
        has_tool_calls = bool(getattr(message, "tool_calls", []))
        if message.type == "ai" and text and not has_tool_calls:
            projected.append(
                ConversationMessage(
                    role="assistant",
                    content=text,
                    tool_calls=tool_calls_from_messages(turn_messages),
                )
            )
            turn_messages = []
    return projected


def title_from_message(message: str) -> str:
    return " ".join(message.split())[:80].rstrip() or "Untitled conversation"


__all__ = [
    "message_text",
    "messages_from_update",
    "project_messages",
    "stream_event_data",
    "title_from_message",
    "tool_calls_from_messages",
    "tool_result_value",
]
