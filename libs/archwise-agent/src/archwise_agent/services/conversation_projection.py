"""Pure projections from LangGraph checkpoints to conversation data."""

from __future__ import annotations

from typing import Any, Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from archwise_agent.core import ArchHypo


def checkpoint_thread_id(checkpoint: Any) -> str | None:
    """Extract a thread id from a LangGraph checkpoint."""

    config = getattr(checkpoint, "config", {})
    configurable = config.get("configurable", {}) if isinstance(config, dict) else {}
    thread_id = configurable.get("thread_id")
    return thread_id if isinstance(thread_id, str) else None


def checkpoint_key(checkpoint: Any) -> str:
    """Return the sortable checkpoint timestamp or id."""

    values = getattr(checkpoint, "checkpoint", {})
    if not isinstance(values, dict):
        return ""
    return str(values.get("ts", values.get("id", "")))


def messages_from_checkpoint(checkpoint: Any) -> list[Any]:
    """Project a checkpoint into user-visible messages."""

    checkpoint_values = getattr(checkpoint, "checkpoint", {})
    if not isinstance(checkpoint_values, dict):
        return []
    return messages_from_values(checkpoint_values.get("channel_values", {}))


def messages_from_values(values: dict[str, Any]) -> list[Any]:
    """Project graph channel values into user-visible messages."""

    existing_messages = values.get("messages")
    if isinstance(existing_messages, list) and existing_messages:
        return user_visible_messages(existing_messages)

    uncertainty = values.get("uncertainty")
    if not isinstance(uncertainty, str) or not uncertainty.strip():
        return []

    messages: list[Any] = [HumanMessage(content=uncertainty)]
    try:
        messages.append(response_message(archhypo_from_value(values.get("result"))))
    except TypeError:
        pass
    return messages


def user_visible_messages(messages: list[Any]) -> list[Any]:
    """Hide internal workflow messages from the conversation projection."""

    has_final_response = any(
        isinstance(message, AIMessage)
        and getattr(message, "name", None) == "response_agent"
        for message in messages
    )
    if has_final_response:
        return [
            message
            for message in messages
            if isinstance(message, HumanMessage)
            or (
                isinstance(message, AIMessage)
                and getattr(message, "name", None) == "response_agent"
            )
        ]

    return [message for message in messages if not _is_internal_message(message)]


def archhypo_from_value(value: Any) -> ArchHypo:
    """Validate an ArchHypo value returned by graph state."""

    if isinstance(value, ArchHypo):
        return value
    if isinstance(value, dict):
        return ArchHypo.model_validate(value)
    raise TypeError("graph did not return an ArchHypo result")


def response_message(archhypo: ArchHypo) -> AIMessage:
    """Build the legacy fallback response for old checkpoints."""

    return AIMessage(content=archhypo.model_dump_json(indent=2))


def message_text(message: BaseMessage | Any) -> str:
    """Extract plain text from a LangChain message."""

    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                text = block.get("text") or block.get("content")
                if isinstance(text, str):
                    parts.append(text)
        return "".join(parts).strip()
    return str(content).strip() if content else ""


def message_role(message: Any) -> Literal["user", "assistant"] | None:
    """Return the public conversation role for a LangChain message."""

    if isinstance(message, HumanMessage) or getattr(message, "type", None) == "human":
        return "user"
    if isinstance(message, AIMessage) or getattr(message, "type", None) == "ai":
        return "assistant"
    return None


def _is_internal_message(message: Any) -> bool:
    """Recognize workflow messages from checkpoints created before response."""

    name = getattr(message, "name", None)
    if name in {"hypothesis_agent", "classifier_agent", "technical_plan_agent"}:
        return True

    text = message_text(message)
    return "{input}" in text and "{/input}" in text


__all__ = [
    "archhypo_from_value",
    "checkpoint_key",
    "checkpoint_thread_id",
    "message_role",
    "message_text",
    "messages_from_checkpoint",
    "messages_from_values",
    "response_message",
    "user_visible_messages",
]
