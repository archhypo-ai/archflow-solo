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


class ArtifactPlanItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str
    pattern: str


class ArtifactSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    cycle_id: str
    thread_id: str
    project_id: str | None
    title: str
    status: str
    outcome: str
    uncertainty: str
    hypothesis_statement: str
    nfr: str | None
    impact: str | None
    uncertainty_level: str | None
    technical_plan_items: list[ArtifactPlanItemResponse]
    created_at: str


class ArtifactHypothesisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str
    statement: str
    justification: str


class ArtifactAssessmentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    nfr: str
    nfr_justification: str
    impact: str
    impact_justification: str
    uncertainty: str
    uncertainty_justification: str


class ArtifactDetailPlanItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str
    objective: str
    description: str
    pattern: str
    tradeoff: str


class ArtifactTechnicalPlanResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    rationale: str
    items: list[ArtifactDetailPlanItemResponse]


class ArtifactDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    cycle_id: str
    thread_id: str
    project_id: str | None
    title: str
    status: Literal["open", "closed"]
    outcome: str
    uncertainty: str
    hypothesis: ArtifactHypothesisResponse
    assessment: ArtifactAssessmentResponse
    technical_plan: ArtifactTechnicalPlanResponse
    created_at: str
    updated_at: str
    review_history: list[dict[str, object]] = Field(default_factory=list)


class ArtifactStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["open", "closed"]


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
    attachments: list[dict[str, str | int]] = Field(default_factory=list)


class ThreadResponse(ThreadSummaryResponse):
    messages: list[ThreadMessageResponse]
    pending_hypothesis_review: dict[str, object] | None = None
    pending_technical_plan_review: dict[str, object] | None = None
    completed_reviews: list[dict[str, object]] = Field(default_factory=list)


__all__ = [
    "ArtifactPlanItemResponse",
    "ArtifactAssessmentResponse",
    "ArtifactDetailPlanItemResponse",
    "ArtifactDetailResponse",
    "ArtifactHypothesisResponse",
    "ArtifactSummaryResponse",
    "ArtifactStatusUpdateRequest",
    "ArtifactTechnicalPlanResponse",
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
