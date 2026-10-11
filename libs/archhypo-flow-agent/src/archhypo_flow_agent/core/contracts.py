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

    @field_validator("thread_id", "message")
    @classmethod
    def reject_blank_values(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value


class ChatResponse(BaseModel):
    """Assistant response for a conversation thread."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    thread_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    message: str = Field(min_length=1)


__all__ = ["ChatRequest", "ChatResponse"]
