"""HTTP response contracts for saved conversations."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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
    pinned: bool


class ThreadUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str | None = Field(default=None, min_length=1, max_length=80)
    pinned: bool | None = None

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        compact = " ".join(value.split())
        if not compact:
            raise ValueError("title must not be blank")
        return compact

    @model_validator(mode="after")
    def require_update(self) -> "ThreadUpdateRequest":
        if self.title is None and self.pinned is None:
            raise ValueError("provide title or pinned")
        return self


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
    "ThreadUpdateRequest",
]
