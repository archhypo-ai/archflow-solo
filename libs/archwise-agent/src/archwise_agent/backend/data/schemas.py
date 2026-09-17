"""Pydantic schemas for the ArchWise HTTP API."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from archwise_agent.config import PACKAGE_VERSION


class ChatRequest(BaseModel):
    """Input for one conversational turn."""

    thread_id: Annotated[str, Field(min_length=1)]
    message: Annotated[str, Field(min_length=1)]
    workspace_id: Annotated[str, Field(min_length=1)] = "default"
    project_id: Annotated[str | None, Field(min_length=1)] = None
    user_id: Annotated[str | None, Field(min_length=1)] = None
    run_id: Annotated[str | None, Field(min_length=1)] = None

    @field_validator("thread_id", "message", "workspace_id")
    @classmethod
    def reject_blank_values(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value

    @field_validator("project_id", "user_id", "run_id")
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


class ChatCancelResponse(BaseModel):
    """Result of requesting cancellation for an active agent run."""

    run_id: str
    cancelled: bool


BACKEND_API_VERSION = PACKAGE_VERSION


class HealthResponse(BaseModel):
    """Backend readiness response."""

    status: Literal["ok"]
    agent_ready: bool
    api_version: str = BACKEND_API_VERSION
    sse_chat: bool = True


class ThreadSummaryResponse(BaseModel):
    """Conversation metadata shown in a client conversation list."""

    thread_id: str
    title: str
    message_count: int
    pinned: bool


class ThreadUpdateRequest(BaseModel):
    """Mutable metadata fields for an existing conversation."""

    title: Annotated[str | None, Field(min_length=1, max_length=80)] = None
    pinned: bool | None = None

    @model_validator(mode="after")
    def require_an_update(self) -> "ThreadUpdateRequest":
        if self.title is None and self.pinned is None:
            raise ValueError("at least one conversation field must be provided")
        return self


class ThreadMessageResponse(BaseModel):
    """User-visible message in a conversation transcript."""

    role: Literal["user", "assistant"]
    content: str


class FolderPathRequest(BaseModel):
    """Local folder selected by the native desktop picker."""

    folder_path: Annotated[str, Field(min_length=1)]


class FolderContextResponse(BaseModel):
    """Persisted folder context shown in a conversation."""

    context_id: str
    thread_id: str
    folder_name: str
    file_count: int
    total_bytes: int


class ThreadResponse(BaseModel):
    """Conversation metadata and transcript."""

    thread_id: str
    title: str
    message_count: int
    messages: list[ThreadMessageResponse]
    pinned: bool
    folder_context: FolderContextResponse | None = None


__all__ = [
    "ChatCancelResponse",
    "ChatRequest",
    "ChatResponse",
    "BACKEND_API_VERSION",
    "FolderContextResponse",
    "FolderPathRequest",
    "HealthResponse",
    "ThreadMessageResponse",
    "ThreadResponse",
    "ThreadSummaryResponse",
    "ThreadUpdateRequest",
]
