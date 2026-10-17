"""Structured contracts for the first ArchHypo workflow slice."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

RequestRoute = Literal[
    "architectural_uncertainty_discovery",
    "hypothesis_formulation",
    "direct_response_generation",
]
RequestIntent = Literal[
    "new_uncertainty",
    "alternative_hypothesis",
    "revise_hypothesis",
    "contextual_question",
    "out_of_scope",
    "clarification",
]
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

_ROUTE_BY_INTENT: dict[str, RequestRoute] = {
    "new_uncertainty": "architectural_uncertainty_discovery",
    "alternative_hypothesis": "hypothesis_formulation",
    "revise_hypothesis": "hypothesis_formulation",
    "contextual_question": "direct_response_generation",
    "out_of_scope": "direct_response_generation",
    "clarification": "direct_response_generation",
}
_LEGACY_INTENT_BY_ROUTE: dict[str, RequestIntent] = {
    "architectural_uncertainty_discovery": "new_uncertainty",
    "hypothesis_formulation": "alternative_hypothesis",
    "direct_response_generation": "contextual_question",
}


class _Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RequestRouting(_Contract):
    """Validated request intent and its corresponding workflow destination."""

    route: RequestRoute = "architectural_uncertainty_discovery"
    intent: RequestIntent

    @model_validator(mode="before")
    @classmethod
    def derive_route_from_intent(cls, value: object) -> object:
        """Keep the graph destination consistent and load legacy checkpoints."""

        if not isinstance(value, dict):
            return value
        values = dict(value)
        intent = values.get("intent")
        if intent is None:
            if "route" not in values:
                return values
            intent = _LEGACY_INTENT_BY_ROUTE.get(str(values["route"]))
            if intent is None:
                return values
            values["intent"] = intent
        route = _ROUTE_BY_INTENT.get(str(intent))
        if route is not None:
            values["route"] = route
        return values


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


class _HumanReviewDecision(_Contract):
    """Shared approve/reject decision with required rejection feedback."""

    decision: Literal["approved", "rejected"]
    reason: str | None = None

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        compact = " ".join(value.split())
        return compact or None

    @model_validator(mode="after")
    def rejected_review_requires_reason(self) -> _HumanReviewDecision:
        if self.decision == "rejected" and self.reason is None:
            raise ValueError("a reason is required when rejecting a review")
        return self


class HypothesisReview(_HumanReviewDecision):
    """Human decision on a formulated hypothesis."""


class TechnicalPlanReview(_HumanReviewDecision):
    """Human decision on an assessed technical plan."""


class HypothesisAssessment(_Contract):
    """Single NFR plus separate impact and uncertainty ratings."""

    nfr: NFR
    nfr_justification: str = Field(min_length=1)
    impact: AssessmentLevel
    impact_justification: str = Field(min_length=1)
    uncertainty: AssessmentLevel
    uncertainty_justification: str = Field(min_length=1)


class CatalogPatternSelection(_Contract):
    """Bounded candidate screen and final reference selection for planning."""

    candidate_patterns: list[ArchHypoPattern] = Field(min_length=1, max_length=5)
    selected_patterns: list[ArchHypoPattern] = Field(min_length=1, max_length=3)
    rationale: str = Field(min_length=1)

    @field_validator("candidate_patterns", "selected_patterns")
    @classmethod
    def reject_duplicate_patterns(
        cls,
        patterns: list[ArchHypoPattern],
    ) -> list[ArchHypoPattern]:
        if len(patterns) != len(set(patterns)):
            raise ValueError("catalog pattern selections must not contain duplicates")
        return patterns

    @model_validator(mode="after")
    def selected_patterns_are_candidates(self) -> CatalogPatternSelection:
        if not set(self.selected_patterns).issubset(self.candidate_patterns):
            raise ValueError("selected patterns must come from the candidate set")
        return self


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
    "CatalogPatternSelection",
    "DiscoveryStatus",
    "Hypothesis",
    "HypothesisReview",
    "HypothesisAssessment",
    "NFR",
    "RequestIntent",
    "RequestRoute",
    "RequestRouting",
    "TechnicalPlan",
    "TechnicalPlanItem",
    "TechnicalPlanReview",
]
