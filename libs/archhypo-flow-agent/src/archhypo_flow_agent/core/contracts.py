"""Validated contracts for the local chat boundary."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .archhypo import Hypothesis, HypothesisReview, TechnicalPlanReview


class ChatRequest(BaseModel):
    """One user message addressed to a conversation thread."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    thread_id: str = Field(min_length=1)
    message: str = ""
    language: Literal["en", "pt-BR"] = "en"
    project_id: str | None = None
    global_context: str = Field(default="", max_length=50_000)
    hypothesis_review: HypothesisReview | None = None
    technical_plan_review: TechnicalPlanReview | None = None

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
        ):
            raise ValueError("message must not be blank")
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
