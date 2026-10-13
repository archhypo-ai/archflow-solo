"""Structured contracts for the first ArchHypo workflow slice."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RequestRoute = Literal["architectural_uncertainty_discovery"]
DiscoveryStatus = Literal["identified", "insufficient_context"]
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


class _Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RequestRouting(_Contract):
    """Fixed first destination for this validation version."""

    route: RequestRoute = "architectural_uncertainty_discovery"


class ArchitecturalUncertaintyDiscovery(_Contract):
    """One central uncertainty extracted from user-provided conversation input."""

    status: DiscoveryStatus
    uncertainty: str | None = Field(default=None, min_length=1)
    rationale: str = Field(min_length=1)
    missing_information: list[str] = Field(default_factory=list, max_length=10)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class Hypothesis(_Contract):
    """One normalized, testable architectural hypothesis."""

    uncertainty: str = Field(min_length=1)
    title: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    justification: str = Field(min_length=1)


class HypothesisAssessment(_Contract):
    """Single NFR plus separate impact and uncertainty ratings."""

    nfr: NFR
    nfr_justification: str = Field(min_length=1)
    impact: AssessmentLevel
    impact_justification: str = Field(min_length=1)
    uncertainty: AssessmentLevel
    uncertainty_justification: str = Field(min_length=1)


class TechnicalPlanItem(_Contract):
    """One action to investigate or manage the assessed hypothesis."""

    title: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    description: str = Field(min_length=1)
    pattern: ArchHypoPattern
    tradeoff: str = Field(min_length=1)


class TechnicalPlan(_Contract):
    """A short ArchHypo plan with one to three actions."""

    items: list[TechnicalPlanItem] = Field(min_length=1, max_length=3)
    rationale: str = Field(min_length=1)


class ArchHypoResult(_Contract):
    """In-memory result passed to the existing response-generation step."""

    uncertainty: str = Field(min_length=1)
    discovery: ArchitecturalUncertaintyDiscovery
    hypothesis: Hypothesis
    assessment: HypothesisAssessment
    technical_plan: TechnicalPlan


__all__ = [
    "ArchHypoPattern",
    "ArchHypoResult",
    "ArchitecturalUncertaintyDiscovery",
    "AssessmentLevel",
    "DiscoveryStatus",
    "Hypothesis",
    "HypothesisAssessment",
    "NFR",
    "RequestRoute",
    "RequestRouting",
    "TechnicalPlan",
    "TechnicalPlanItem",
]
