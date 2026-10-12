"""Validated events exchanged between the agent backend and frontend."""

from __future__ import annotations

from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, Field, TypeAdapter


class EventBase(BaseModel):
    """Fields shared by every wire event."""

    protocol_version: Literal[1] = 1
    run_id: str = Field(min_length=1)
    thread_id: str = Field(min_length=1)


class ConversationStartedEvent(EventBase):
    type: Literal["conversation_started"] = "conversation_started"
    title: str
    user_message: str
    project_id: str | None


class PhaseEvent(EventBase):
    type: Literal["phase"] = "phase"
    phase: str = Field(min_length=1)


class TextDeltaEvent(EventBase):
    type: Literal["text_delta"] = "text_delta"
    text: str


class DoneEvent(EventBase):
    type: Literal["done"] = "done"
    status: Literal["completed"] = "completed"


class CancelledEvent(EventBase):
    type: Literal["cancelled"] = "cancelled"
    status: Literal["cancelled"] = "cancelled"
    reason: str | None = None


class ErrorEvent(EventBase):
    type: Literal["error"] = "error"
    message: str = Field(min_length=1)


class ToolCallStartEvent(EventBase):
    type: Literal["tool_call_start"] = "tool_call_start"
    tool_call_id: str = Field(min_length=1)
    name: str = Field(min_length=1)


class ToolCallDeltaEvent(EventBase):
    type: Literal["tool_call_delta"] = "tool_call_delta"
    tool_call_id: str = Field(min_length=1)
    text: str


class ToolResultEvent(EventBase):
    type: Literal["tool_result"] = "tool_result"
    tool_call_id: str = Field(min_length=1)
    output: object


class InterruptEvent(EventBase):
    type: Literal["interrupt"] = "interrupt"
    interrupt_id: str = Field(min_length=1)
    message: str = Field(min_length=1)
    payload: dict[str, object] | None = None


AgentEvent: TypeAlias = Annotated[
    ConversationStartedEvent
    | PhaseEvent
    | TextDeltaEvent
    | DoneEvent
    | CancelledEvent
    | ErrorEvent
    | ToolCallStartEvent
    | ToolCallDeltaEvent
    | ToolResultEvent
    | InterruptEvent,
    Field(discriminator="type"),
]

_AGENT_EVENT_ADAPTER = TypeAdapter(AgentEvent)


def agent_event_data(event: AgentEvent) -> dict[str, object]:
    """Serialize an event into the JSON object carried by SSE data."""

    return _AGENT_EVENT_ADAPTER.dump_python(event, mode="json")


def phase_event(*, run_id: str, thread_id: str, phase: str) -> PhaseEvent:
    return PhaseEvent(run_id=run_id, thread_id=thread_id, phase=phase)


def text_delta_event(*, run_id: str, thread_id: str, text: str) -> TextDeltaEvent:
    return TextDeltaEvent(run_id=run_id, thread_id=thread_id, text=text)


def done_event(*, run_id: str, thread_id: str) -> DoneEvent:
    return DoneEvent(run_id=run_id, thread_id=thread_id)


def cancelled_event(
    *, run_id: str, thread_id: str, reason: str | None = None
) -> CancelledEvent:
    return CancelledEvent(
        run_id=run_id,
        thread_id=thread_id,
        reason=reason,
    )


def error_event(*, run_id: str, thread_id: str, message: str) -> ErrorEvent:
    return ErrorEvent(
        run_id=run_id,
        thread_id=thread_id,
        message=message,
    )
