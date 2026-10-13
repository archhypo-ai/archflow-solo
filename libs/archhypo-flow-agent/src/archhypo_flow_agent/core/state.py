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
    RequestRouting,
    TechnicalPlan,
)


class AgentState(TypedDict):
    """Conversation plus the intermediate data for one ArchHypo run."""

    messages: Annotated[list[AnyMessage], add_messages]
    routing: NotRequired[RequestRouting | None]
    discovery: NotRequired[ArchitecturalUncertaintyDiscovery | None]
    uncertainty: NotRequired[str | None]
    hypothesis: NotRequired[Hypothesis | None]
    assessment: NotRequired[HypothesisAssessment | None]
    technical_plan: NotRequired[TechnicalPlan | None]
    result: NotRequired[ArchHypoResult | None]


__all__ = ["AgentState"]
