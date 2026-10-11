"""HTTP response contracts for saved conversations."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["ok"] = "ok"
    agent_ready: bool
    configuration_error: str | None = None


class ThreadSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    thread_id: str
    title: str
    message_count: int
    updated_at: str


class ThreadMessageResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role: Literal["user", "assistant"]
    content: str


class ThreadResponse(ThreadSummaryResponse):
    messages: list[ThreadMessageResponse]


__all__ = [
    "HealthResponse",
    "ThreadMessageResponse",
    "ThreadResponse",
    "ThreadSummaryResponse",
]
