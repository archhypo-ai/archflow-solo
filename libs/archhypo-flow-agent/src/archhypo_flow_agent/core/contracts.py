"""Validated contracts for the local chat boundary."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatRequest(BaseModel):
    """One user message addressed to a conversation thread."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    thread_id: str = Field(min_length=1)
    message: str = Field(min_length=1)
    language: Literal["en", "pt-BR"] = "en"
    project_id: str | None = None
    global_context: str = Field(default="", max_length=50_000)

    @field_validator("thread_id", "message")
    @classmethod
    def reject_blank_values(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value


class ToolCallRecord(BaseModel):
    """A completed tool invocation included in the visible conversation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    args: dict[str, object]
    result: object | None = None
    is_error: bool = False


class ChatResponse(BaseModel):
    """Assistant response for a conversation thread."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    thread_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    message: str = Field(min_length=1)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)


__all__ = ["ChatRequest", "ChatResponse", "ToolCallRecord"]
