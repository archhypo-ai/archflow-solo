"""HTTP response contracts for saved conversations."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from archhypo_flow_agent.core import ToolCallRecord


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
    project_id: str | None
    preview: str


class ProjectResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    name: str
    icon: str
    color: str
    instructions: str
    created_at: str
    updated_at: str


class ProjectCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=80)
    icon: str = Field(min_length=1, max_length=40)
    color: Literal[
        "neutral", "red", "orange", "yellow", "green", "blue", "purple", "pink"
    ]
    instructions: str = ""

    @field_validator("id", "name", "icon")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        compact = " ".join(value.split())
        if not compact:
            raise ValueError("field must not be blank")
        return compact


class ProjectUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1, max_length=80)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        compact = " ".join(value.split())
        if not compact:
            raise ValueError("name must not be blank")
        return compact


class ProjectSettingsUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1, max_length=80)
    icon: str = Field(min_length=1, max_length=40)
    color: Literal[
        "neutral", "red", "orange", "yellow", "green", "blue", "purple", "pink"
    ]
    instructions: str = ""

    @field_validator("name", "icon")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        compact = " ".join(value.split())
        if not compact:
            raise ValueError("field must not be blank")
        return compact


class ThreadProjectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    project_id: str | None


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
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)


class ThreadResponse(ThreadSummaryResponse):
    messages: list[ThreadMessageResponse]
    pending_hypothesis_review: dict[str, object] | None = None


__all__ = [
    "HealthResponse",
    "ProjectCreateRequest",
    "ProjectResponse",
    "ProjectSettingsUpdateRequest",
    "ProjectUpdateRequest",
    "ThreadMessageResponse",
    "ThreadResponse",
    "ThreadSummaryResponse",
    "ThreadProjectRequest",
    "ThreadUpdateRequest",
]
