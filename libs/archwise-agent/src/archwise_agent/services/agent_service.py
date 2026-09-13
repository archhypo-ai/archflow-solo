"""Application-facing service for the ArchWise agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.checkpoint.base import BaseCheckpointSaver

from archwise_agent.agents import build_archwise_agent
from archwise_agent.config import AgentSettings


@dataclass(frozen=True, slots=True)
class AgentTurn:
    """Assistant response returned by one agent turn."""

    thread_id: str
    message: AIMessage

    @property
    def text(self) -> str:
        return _message_text(self.message)


@dataclass(frozen=True, slots=True)
class ConversationMessage:
    """User-visible message from a checkpointed conversation."""

    role: Literal["user", "assistant"]
    content: str


@dataclass(frozen=True, slots=True)
class ConversationSummary:
    """Metadata used to list available conversations."""

    thread_id: str
    title: str
    message_count: int


@dataclass(frozen=True, slots=True)
class Conversation:
    """Conversation metadata and its user-visible messages."""

    thread_id: str
    title: str
    message_count: int
    messages: list[ConversationMessage]


class AgentService:
    """Keep the compiled agent alive and provide a stable application API."""

    def __init__(
        self,
        *,
        configuration: AgentSettings | None = None,
        model: BaseChatModel | None = None,
        checkpointer: BaseCheckpointSaver | None = None,
    ) -> None:
        self._agent = build_archwise_agent(
            model=model,
            configuration=configuration,
            checkpointer=checkpointer,
        )

    def send(self, *, thread_id: str, message: str) -> AgentTurn:
        """Send a message while preserving the supplied checkpoint thread."""

        if not thread_id.strip():
            raise ValueError("thread_id must not be empty")
        if not message.strip():
            raise ValueError("message must not be empty")

        result: dict[str, Any] = self._agent.invoke(
            {"messages": [HumanMessage(content=message)]},
            {"configurable": {"thread_id": thread_id}},
        )
        response = result["messages"][-1]
        if not isinstance(response, AIMessage):
            raise TypeError("agent did not return an AI message")
        return AgentTurn(thread_id=thread_id, message=response)

    def list_conversations(self) -> list[ConversationSummary]:
        """List latest checkpoint state for every known thread."""

        latest: dict[str, Any] = {}
        for item in self._agent.checkpointer.list(None):
            thread_id = _thread_id_from_checkpoint(item)
            if not thread_id:
                continue
            current = latest.get(thread_id)
            if current is None or _checkpoint_key(item) > _checkpoint_key(current):
                latest[thread_id] = item

        conversations = [
            _conversation_summary(
                thread_id,
                _messages_from_checkpoint(item),
            )
            for thread_id, item in latest.items()
        ]
        return sorted(conversations, key=lambda item: item.title.casefold())

    def get_conversation(self, thread_id: str) -> Conversation | None:
        """Load one conversation from its checkpoint thread."""

        if not thread_id.strip():
            raise ValueError("thread_id must not be empty")

        state = self._agent.get_state(
            {"configurable": {"thread_id": thread_id}}
        )
        values = state.values if isinstance(state.values, dict) else {}
        messages = values.get("messages", [])
        if not messages:
            return None

        conversation = _conversation_summary(thread_id, messages)
        return Conversation(
            thread_id=conversation.thread_id,
            title=conversation.title,
            message_count=conversation.message_count,
            messages=_conversation_messages(messages),
        )

    @property
    def agent(self):
        """Expose the compiled agent to future streaming/resume adapters."""

        return self._agent


def _thread_id_from_checkpoint(checkpoint: Any) -> str | None:
    config = getattr(checkpoint, "config", {})
    configurable = config.get("configurable", {}) if isinstance(config, dict) else {}
    thread_id = configurable.get("thread_id")
    return thread_id if isinstance(thread_id, str) else None


def _checkpoint_key(checkpoint: Any) -> str:
    values = getattr(checkpoint, "checkpoint", {})
    if not isinstance(values, dict):
        return ""
    return str(values.get("ts", values.get("id", "")))


def _messages_from_checkpoint(checkpoint: Any) -> list[Any]:
    values = getattr(checkpoint, "checkpoint", {})
    if not isinstance(values, dict):
        return []
    channels = values.get("channel_values", {})
    if not isinstance(channels, dict):
        return []
    messages = channels.get("messages", [])
    return list(messages) if isinstance(messages, list) else []


def _conversation_summary(
    thread_id: str,
    messages: list[Any],
) -> ConversationSummary:
    title = next(
        (
            _message_text(message)
            for message in messages
            if _message_role(message) == "user" and _message_text(message)
        ),
        "Untitled conversation",
    )
    return ConversationSummary(
        thread_id=thread_id,
        title=_truncate(title),
        message_count=len(messages),
    )


def _conversation_messages(messages: list[Any]) -> list[ConversationMessage]:
    result: list[ConversationMessage] = []
    for message in messages:
        role = _message_role(message)
        text = _message_text(message)
        if role in ("user", "assistant") and text:
            result.append(ConversationMessage(role=role, content=text))
    return result


def _message_role(message: Any) -> Literal["user", "assistant"] | None:
    if isinstance(message, HumanMessage) or getattr(message, "type", None) == "human":
        return "user"
    if isinstance(message, AIMessage) or getattr(message, "type", None) == "ai":
        return "assistant"
    return None


def _message_text(message: BaseMessage | Any) -> str:
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


def _truncate(value: str, limit: int = 60) -> str:
    return value if len(value) <= limit else f"{value[: limit - 1].rstrip()}…"


__all__ = [
    "AgentService",
    "AgentTurn",
    "Conversation",
    "ConversationMessage",
    "ConversationSummary",
]
