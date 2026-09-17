"""Pydantic contracts for the ArchHypo workflow."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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


class Hypothesis(_DomainModel):
    """One testable architectural hypothesis."""

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
    """Three to five actions grounded in ArchHypo patterns."""

    items: list[TechnicalPlanItem] = Field(min_length=3, max_length=5)
    rationale: str = Field(min_length=1)


class ArchHypo(_DomainModel):
    """Complete result produced by the ArchHypo workflow."""

    uncertainty: str = Field(min_length=1)
    hypothesis: Hypothesis
    classification: HypothesisClassification
    technical_plan: TechnicalPlan


__all__ = [
    "ArchHypo",
    "ArchHypoPattern",
    "AssessmentLevel",
    "Hypothesis",
    "HypothesisClassification",
    "NFR",
    "TechnicalPlan",
    "TechnicalPlanItem",
]
