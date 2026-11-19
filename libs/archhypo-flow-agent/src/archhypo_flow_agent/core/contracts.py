"""Validated contracts for the local chat boundary."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .archhypo import Hypothesis, HypothesisReview, TechnicalPlanReview


class DocumentAttachment(BaseModel):
    """A user-approved document sent with one chat message."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str = Field(min_length=1, max_length=255)
    data: str = Field(min_length=1, max_length=7_000_000)
    folder_id: str | None = Field(default=None, min_length=1, max_length=128)
    folder_name: str | None = Field(default=None, min_length=1, max_length=255)

    @model_validator(mode="after")
    def require_folder_pair(self) -> "DocumentAttachment":
        if (self.folder_id is None) != (self.folder_name is None):
            raise ValueError("folder_id and folder_name must be provided together")
        return self


class ChatRequest(BaseModel):
    review_interrupt_id: str | None = None
    """One user message addressed to a conversation thread."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    thread_id: str = Field(min_length=1)
    message: str = ""
    language: Literal["en", "pt-BR"] = "en"
    project_id: str | None = None
    global_context: str = Field(default="", max_length=50_000)
    hitl_enabled: bool = True
    hypothesis_review: HypothesisReview | None = None
    technical_plan_review: TechnicalPlanReview | None = None
    attachments: list[DocumentAttachment] = Field(default_factory=list, max_length=20)

    @field_validator("thread_id")
    @classmethod
    def reject_blank_values(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value

    @model_validator(mode="after")
    def accept_one_review_decision(self) -> "ChatRequest":
        if (
            self.hypothesis_review is not None
            and self.technical_plan_review is not None
        ):
            raise ValueError(
                "only one human-review decision can be submitted at a time"
            )
        if (
            not self.message.strip()
            and self.hypothesis_review is None
            and self.technical_plan_review is None
            and not self.attachments
        ):
            raise ValueError("message must not be blank")
        if self.attachments and (self.hypothesis_review or self.technical_plan_review):
            raise ValueError("documents cannot be attached to a review decision")
        return self


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
    pending_hypothesis_review: Hypothesis | None = None
    pending_technical_plan_review: dict[str, object] | None = None


__all__ = ["ChatRequest", "ChatResponse", "ToolCallRecord"]
