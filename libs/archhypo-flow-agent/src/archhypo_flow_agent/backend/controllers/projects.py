"""Project metadata HTTP controller."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Response

from archhypo_flow_agent.backend.dependencies import AgentServiceDependency
from archhypo_flow_agent.backend.schemas import (
    ProjectCreateRequest,
    ProjectResponse,
    ProjectSettingsUpdateRequest,
    ProjectUpdateRequest,
)

router = APIRouter(prefix="/api", tags=["projects"])


@router.get("/projects", response_model=list[ProjectResponse])
def list_projects(agent_service: AgentServiceDependency) -> list[ProjectResponse]:
    return [
        ProjectResponse(
            id=project.id,
            name=project.name,
            icon=project.icon,
            color=project.color,
            instructions=project.instructions,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
        for project in agent_service.list_projects()
    ]


@router.post("/projects", response_model=ProjectResponse, status_code=201)
def create_project(
    payload: ProjectCreateRequest,
    agent_service: AgentServiceDependency,
) -> ProjectResponse:
    project = agent_service.create_project(
        project_id=payload.id,
        name=payload.name,
        icon=payload.icon,
        color=payload.color,
        instructions=payload.instructions,
    )
    return ProjectResponse(
        id=project.id,
        name=project.name,
        icon=project.icon,
        color=project.color,
        instructions=project.instructions,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
def rename_project(
    project_id: Annotated[str, Path(min_length=1)],
    payload: ProjectUpdateRequest,
    agent_service: AgentServiceDependency,
) -> ProjectResponse:
    project = agent_service.rename_project(project_id, payload.name)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return ProjectResponse(
        id=project.id,
        name=project.name,
        icon=project.icon,
        color=project.color,
        instructions=project.instructions,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.put("/projects/{project_id}", response_model=ProjectResponse)
def update_project_settings(
    project_id: Annotated[str, Path(min_length=1)],
    payload: ProjectSettingsUpdateRequest,
    agent_service: AgentServiceDependency,
) -> ProjectResponse:
    project = agent_service.update_project_settings(
        project_id,
        name=payload.name,
        icon=payload.icon,
        color=payload.color,
        instructions=payload.instructions,
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return ProjectResponse(
        id=project.id,
        name=project.name,
        icon=project.icon,
        color=project.color,
        instructions=project.instructions,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(
    project_id: Annotated[str, Path(min_length=1)],
    agent_service: AgentServiceDependency,
) -> Response:
    if not agent_service.delete_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found.")
    return Response(status_code=204)


__all__ = ["router"]
