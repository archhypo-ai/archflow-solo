"""Read-only ArchHypo artifact listing endpoint."""

from typing import Annotated

from fastapi import APIRouter, Query

from archhypo_flow_agent.backend.dependencies import AgentServiceDependency
from archhypo_flow_agent.backend.schemas import (
    ArtifactPlanItemResponse,
    ArtifactSummaryResponse,
)
from archhypo_flow_agent.persistence.artifacts import ArchHypoArtifactRecord

router = APIRouter(prefix="/api", tags=["artifacts"])


@router.get("/artifacts", response_model=list[ArtifactSummaryResponse])
def list_artifacts(
    agent_service: AgentServiceDependency,
    project_id: Annotated[str | None, Query(min_length=1)] = None,
) -> list[ArtifactSummaryResponse]:
    """List artifact summaries globally or for one project."""

    return [
        _to_summary(artifact)
        for artifact in agent_service.list_artifacts(project_id=project_id)
    ]


def _to_summary(artifact: ArchHypoArtifactRecord) -> ArtifactSummaryResponse:
    result = artifact.result
    hypothesis = _as_mapping(result.get("hypothesis"))
    assessment = _as_mapping(result.get("assessment"))
    technical_plan = _as_mapping(result.get("technical_plan"))
    raw_items = technical_plan.get("items", [])
    items = raw_items if isinstance(raw_items, list) else []

    return ArtifactSummaryResponse(
        id=artifact.id,
        cycle_id=artifact.cycle_id,
        thread_id=artifact.thread_id,
        project_id=artifact.project_id,
        title=artifact.title,
        status=artifact.status,
        outcome=artifact.outcome,
        uncertainty=_as_string(result.get("uncertainty")),
        hypothesis_statement=_as_string(hypothesis.get("statement")),
        nfr=_as_optional_string(assessment.get("nfr")),
        impact=_as_optional_string(assessment.get("impact")),
        uncertainty_level=_as_optional_string(assessment.get("uncertainty")),
        technical_plan_items=[
            ArtifactPlanItemResponse(
                title=_as_string(item.get("title")),
                pattern=_as_string(item.get("pattern")),
            )
            for raw_item in items
            if (item := _as_mapping(raw_item))
        ],
        created_at=artifact.created_at,
    )


def _as_mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _as_string(value: object) -> str:
    return value if isinstance(value, str) else ""


def _as_optional_string(value: object) -> str | None:
    return value if isinstance(value, str) else None


__all__ = ["router"]
