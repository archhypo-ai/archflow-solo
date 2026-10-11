"""LangGraph state for the ArchHypo workflow."""

from typing import Annotated, NotRequired

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from .models import (
    ArchHypo,
    Hypothesis,
    HypothesisClassification,
    RequestRouting,
    TechnicalPlan,
    UncertaintyDiscoveryReport,
)


class ArchHypoState(TypedDict):
    """State shared by the linear ArchHypo workflow."""

    messages: Annotated[list[AnyMessage], add_messages]
    uncertainty: str
    routing: NotRequired[RequestRouting | None]
    discovery: NotRequired[UncertaintyDiscoveryReport | None]
    response: NotRequired[str | None]
    hypothesis: NotRequired[Hypothesis | None]
    classification: NotRequired[HypothesisClassification | None]
    technical_plan: NotRequired[TechnicalPlan | None]
    result: NotRequired[ArchHypo | None]


__all__ = ["ArchHypoState"]
