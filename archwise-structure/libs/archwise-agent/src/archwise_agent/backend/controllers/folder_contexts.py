"""Folder-context HTTP controller."""

from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Path, Response, UploadFile

from archwise_agent.backend.data import FolderContextResponse, FolderPathRequest
from archwise_agent.backend.dependencies import AgentServiceDependency
from archwise_agent.services import FolderContext

router = APIRouter(prefix="/api", tags=["folder-contexts"])


def folder_context_response(context: FolderContext) -> FolderContextResponse:
    """Convert an application folder context into an API response."""

    return FolderContextResponse(
        context_id=context.context_id,
        thread_id=context.thread_id,
        folder_name=context.folder_name,
        file_count=context.file_count,
        total_bytes=context.total_bytes,
    )


@router.post(
    "/threads/{thread_id}/folder-context",
    response_model=FolderContextResponse,
)
def attach_folder_context(
    thread_id: Annotated[str, Path(min_length=1)],
    folder_name: Annotated[str, Form()],
    files: Annotated[list[UploadFile], File(...)],
    agent_service: AgentServiceDependency,
) -> FolderContextResponse:
    """Upload and persist one read-only folder context for a thread."""

    try:
        context = agent_service.attach_folder_context(
            thread_id=thread_id,
            folder_name=folder_name,
            files=((upload.filename or "", upload.file) for upload in files),
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return folder_context_response(context)


@router.post(
    "/threads/{thread_id}/folder-context/path",
    response_model=FolderContextResponse,
)
def attach_folder_context_path(
    thread_id: Annotated[str, Path(min_length=1)],
    payload: FolderPathRequest,
    agent_service: AgentServiceDependency,
) -> FolderContextResponse:
    """Persist a folder selected by the native desktop picker."""

    try:
        context = agent_service.attach_folder_context_path(
            thread_id=thread_id,
            folder_path=payload.folder_path,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return folder_context_response(context)


@router.delete("/threads/{thread_id}/folder-context", status_code=204)
def delete_folder_context(
    thread_id: Annotated[str, Path(min_length=1)],
    agent_service: AgentServiceDependency,
) -> Response:
    """Remove the folder context attached to a thread."""

    try:
        deleted = agent_service.delete_folder_context(thread_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if not deleted:
        raise HTTPException(status_code=404, detail="Folder context not found.")
    return Response(status_code=204)


__all__ = ["folder_context_response", "router"]
