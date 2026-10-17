"""State shared by the ArchHypo Flow graph."""

from typing import Annotated, NotRequired

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from .archhypo import (
    ArchHypoResult,
    ArchitecturalUncertaintyDiscovery,
    Hypothesis,
    HypothesisAssessment,
    HypothesisReview,
    RequestRouting,
    TechnicalPlan,
    TechnicalPlanReview,
)


class AgentState(TypedDict):
    """Conversation plus the intermediate data for one ArchHypo run."""

    messages: Annotated[list[AnyMessage], add_messages]
    routing: NotRequired[RequestRouting | None]
    discovery: NotRequired[ArchitecturalUncertaintyDiscovery | None]
    uncertainty: NotRequired[str | None]
    hypothesis: NotRequired[Hypothesis | None]
    formulation_question: NotRequired[str | None]
    hypothesis_review: NotRequired[HypothesisReview | None]
    hypothesis_feedback: NotRequired[str | None]
    assessment: NotRequired[HypothesisAssessment | None]
    technical_plan: NotRequired[TechnicalPlan | None]
    technical_plan_review: NotRequired[TechnicalPlanReview | None]
    technical_plan_feedback: NotRequired[str | None]
    review_history: NotRequired[list[dict[str, object]]]
    result: NotRequired[ArchHypoResult | None]
    result_history: NotRequired[list[ArchHypoResult]]


__all__ = ["AgentState"]
