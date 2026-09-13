"""Pydantic schemas for the ArchWise HTTP API."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

from archwise_agent.config import PACKAGE_VERSION


class ChatRequest(BaseModel):
    """Input for one conversational turn."""

    thread_id: Annotated[str, Field(min_length=1)]
    message: Annotated[str, Field(min_length=1)]
    workspace_id: Annotated[str, Field(min_length=1)] = "default"
    project_id: Annotated[str | None, Field(min_length=1)] = None
    user_id: Annotated[str | None, Field(min_length=1)] = None

    @field_validator("thread_id", "message", "workspace_id")
    @classmethod
    def reject_blank_values(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value

    @field_validator("project_id", "user_id")
    @classmethod
    def reject_blank_optional_values(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("value must not be blank")
        return value


class ChatResponse(BaseModel):
    """Output returned after one completed agent turn."""

    thread_id: str
    message: str
    status: Literal["completed"] = "completed"


BACKEND_API_VERSION = PACKAGE_VERSION


class HealthResponse(BaseModel):
    """Backend readiness response."""

    status: Literal["ok"]
    agent_ready: bool
    api_version: str = BACKEND_API_VERSION


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
    "BACKEND_API_VERSION",
    "HealthResponse",
    "ThreadMessageResponse",
    "ThreadResponse",
    "ThreadSummaryResponse",
]
