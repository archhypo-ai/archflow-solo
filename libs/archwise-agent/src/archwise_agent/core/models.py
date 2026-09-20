"""Pydantic contracts for the ArchHypo workflow."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RequestRoute = Literal[
    "direct_response",
    "archwise_workflow",
    "uncertainty_discovery",
]

DiscoveryStatus = Literal[
    "found",
    "not_found",
    "insufficient_context",
    "failed",
]

DiscoverySourceType = Literal[
    "code",
    "configuration",
    "documentation",
    "rfc",
    "adr",
    "other",
]

NFR = Literal[
    "Performance",
    "Security",
    "Reliability",
    "Flexibility",
    "Usability",
    "Productivity",
]

AssessmentLevel = Literal["Very Low", "Low", "Medium", "High", "Very High"]

ArchHypoPattern = Literal[
    "Architectural Spike",
    "Architectural Trigger",
    "Bring the Specialist",
    "Continuous Inspection",
    "Learning from Experiments",
    "Plan for Preparation",
    "Postpone Uncertain Decisions",
    "Protective Guideline",
    "Quality Checkpoint",
    "Software Analytics (What You Need to Know)",
    "Technical Debt Management",
    "Tracer Bullets",
]


class _DomainModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RequestRouting(_DomainModel):
    """Destination selected for the current user request."""

    route: RequestRoute
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    probabilities: dict[str, float] | None = None


class UserResponse(_DomainModel):
    """Human-facing response returned by the final response agent."""

    message: str = Field(min_length=1)


class DiscoveryEvidence(_DomainModel):
    """One repository or document observation supporting discovery."""

    path: str = Field(min_length=1)
    location: str = Field(default="unknown", min_length=1)
    source_type: DiscoverySourceType
    observation: str = Field(min_length=1)


class DiscoveryCandidate(_DomainModel):
    """A possible architectural uncertainty found during investigation."""

    uncertainty: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


class UncertaintyDiscoveryReport(_DomainModel):
    """Structured result produced by the workspace investigation agent."""

    status: DiscoveryStatus
    summary: str = Field(min_length=1)
    candidates: list[DiscoveryCandidate] = Field(default_factory=list, max_length=3)
    evidence: list[DiscoveryEvidence] = Field(default_factory=list, max_length=20)
    consulted_sources: list[str] = Field(default_factory=list, max_length=20)
    missing_information: list[str] = Field(default_factory=list, max_length=10)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class Hypothesis(_DomainModel):
    """One normalized uncertainty and its testable hypothesis."""

    uncertainty: str = Field(
        min_length=1,
        description="Short normalized architectural uncertainty.",
    )
    title: str = Field(min_length=1, description="Short hypothesis title.")
    statement: str = Field(
        min_length=1,
        description="One declarative and testable architectural assertion.",
    )
    justification: str = Field(
        min_length=1,
        description="Why this hypothesis represents the supplied uncertainty.",
    )


class HypothesisClassification(_DomainModel):
    """NFR, impact, and uncertainty assessment for one hypothesis."""

    nfr: NFR
    nfr_justification: str = Field(min_length=1)
    impact: AssessmentLevel
    impact_justification: str = Field(min_length=1)
    uncertainty: AssessmentLevel
    uncertainty_justification: str = Field(min_length=1)


class TechnicalPlanItem(_DomainModel):
    """One action for reducing an architectural uncertainty."""

    title: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    description: str = Field(min_length=1)
    pattern: ArchHypoPattern
    tradeoff: str = Field(min_length=1)


class TechnicalPlan(_DomainModel):
    """One to three actions grounded in ArchHypo patterns."""

    items: list[TechnicalPlanItem] = Field(min_length=1, max_length=3)
    rationale: str = Field(min_length=1)


class ArchHypo(_DomainModel):
    """Complete result produced by the ArchHypo workflow."""

    uncertainty: str = Field(min_length=1)
    hypothesis: Hypothesis
    classification: HypothesisClassification
    technical_plan: TechnicalPlan
    discovery: UncertaintyDiscoveryReport | None = None


__all__ = [
    "ArchHypo",
    "ArchHypoPattern",
    "AssessmentLevel",
    "RequestRoute",
    "RequestRouting",
    "UserResponse",
    "Hypothesis",
    "HypothesisClassification",
    "NFR",
    "TechnicalPlan",
    "TechnicalPlanItem",
]
