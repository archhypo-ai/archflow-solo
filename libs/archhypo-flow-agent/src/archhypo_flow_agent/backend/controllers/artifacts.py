"""ArchHypo artifact listing and detail endpoints."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query

from archhypo_flow_agent.backend.dependencies import AgentServiceDependency
from archhypo_flow_agent.backend.schemas import (
    ArtifactAssessmentResponse,
    ArtifactDetailPlanItemResponse,
    ArtifactDetailResponse,
    ArtifactHypothesisResponse,
    ArtifactPlanItemResponse,
    ArtifactStatusUpdateRequest,
    ArtifactSummaryResponse,
    ArtifactTechnicalPlanResponse,
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


@router.get("/artifacts/{artifact_id}", response_model=ArtifactDetailResponse)
def get_artifact(
    agent_service: AgentServiceDependency,
    artifact_id: Annotated[str, Path(min_length=1)],
) -> ArtifactDetailResponse:
    """Return a full artifact result for its detail view."""

    artifact = agent_service.get_artifact(artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return _to_detail(artifact)


@router.patch("/artifacts/{artifact_id}", response_model=ArtifactDetailResponse)
def update_artifact_status(
    request: ArtifactStatusUpdateRequest,
    agent_service: AgentServiceDependency,
    artifact_id: Annotated[str, Path(min_length=1)],
) -> ArtifactDetailResponse:
    """Update an artifact's workflow status."""

    artifact = agent_service.update_artifact_status(artifact_id, request.status)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return _to_detail(artifact)


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


def _to_detail(artifact: ArchHypoArtifactRecord) -> ArtifactDetailResponse:
    result = artifact.result
    hypothesis = _as_mapping(result.get("hypothesis"))
    assessment = _as_mapping(result.get("assessment"))
    technical_plan = _as_mapping(result.get("technical_plan"))
    raw_items = technical_plan.get("items", [])
    items = raw_items if isinstance(raw_items, list) else []

    return ArtifactDetailResponse(
        id=artifact.id,
        cycle_id=artifact.cycle_id,
        thread_id=artifact.thread_id,
        project_id=artifact.project_id,
        title=artifact.title,
        status=artifact.status,
        outcome=artifact.outcome,
        uncertainty=_as_string(result.get("uncertainty")),
        hypothesis=ArtifactHypothesisResponse(
            title=_as_string(hypothesis.get("title")),
            statement=_as_string(hypothesis.get("statement")),
            justification=_as_string(hypothesis.get("justification")),
        ),
        assessment=ArtifactAssessmentResponse(
            nfr=_as_string(assessment.get("nfr")),
            nfr_justification=_as_string(assessment.get("nfr_justification")),
            impact=_as_string(assessment.get("impact")),
            impact_justification=_as_string(
                assessment.get("impact_justification")
            ),
            uncertainty=_as_string(assessment.get("uncertainty")),
            uncertainty_justification=_as_string(
                assessment.get("uncertainty_justification")
            ),
        ),
        technical_plan=ArtifactTechnicalPlanResponse(
            rationale=_as_string(technical_plan.get("rationale")),
            items=[
                ArtifactDetailPlanItemResponse(
                    title=_as_string(item.get("title")),
                    objective=_as_string(item.get("objective")),
                    description=_as_string(item.get("description")),
                    pattern=_as_string(item.get("pattern")),
                    tradeoff=_as_string(item.get("tradeoff")),
                )
                for raw_item in items
                if (item := _as_mapping(raw_item))
            ],
        ),
        created_at=artifact.created_at,
        updated_at=artifact.updated_at,
    )


def _as_mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _as_string(value: object) -> str:
    return value if isinstance(value, str) else ""


def _as_optional_string(value: object) -> str | None:
    return value if isinstance(value, str) else None


__all__ = ["router"]
