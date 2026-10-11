"""Validated contracts for the local chat boundary."""

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """One user message addressed to a conversation thread."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    thread_id: str = Field(min_length=1)
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    """Assistant response for a conversation thread."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    thread_id: str = Field(min_length=1)
    message: str = Field(min_length=1)


__all__ = ["ChatRequest", "ChatResponse"]
