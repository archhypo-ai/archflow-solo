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


__all__ = ["ChatRequest", "ChatResponse", "HealthResponse"]
