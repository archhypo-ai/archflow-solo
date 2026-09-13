"""Pydantic schemas for the ArchWise HTTP API."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    """Input for one conversational turn."""

    thread_id: Annotated[str, Field(min_length=1)]
    message: Annotated[str, Field(min_length=1)]

    @field_validator("thread_id", "message")
    @classmethod
    def reject_blank_values(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value


class ChatResponse(BaseModel):
    """Output returned after one completed agent turn."""

    thread_id: str
    message: str
    status: Literal["completed"] = "completed"


class HealthResponse(BaseModel):
    """Backend readiness response."""

    status: Literal["ok"]
    agent_ready: bool


class ThreadSummaryResponse(BaseModel):
    """Conversation metadata shown in a client conversation list."""

    thread_id: str
    title: str
    message_count: int


class ThreadMessageResponse(BaseModel):
    """User-visible message in a conversation transcript."""

    role: Literal["user", "assistant"]
    content: str


class ThreadResponse(BaseModel):
    """Conversation metadata and transcript."""

    thread_id: str
    title: str
    message_count: int
    messages: list[ThreadMessageResponse]


__all__ = [
    "ChatRequest",
    "ChatResponse",
    "HealthResponse",
    "ThreadMessageResponse",
    "ThreadResponse",
    "ThreadSummaryResponse",
]
