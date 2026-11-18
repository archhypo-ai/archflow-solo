"""Conversation history HTTP controller."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Response

from archhypo_flow_agent.backend.dependencies import AgentServiceDependency
from archhypo_flow_agent.backend.schemas import (
    ThreadMessageResponse,
    ThreadProjectRequest,
    ThreadResponse,
    ThreadSummaryResponse,
    ThreadUpdateRequest,
)

router = APIRouter(prefix="/api", tags=["threads"])


@router.get("/threads", response_model=list[ThreadSummaryResponse])
def list_threads(
    agent_service: AgentServiceDependency,
) -> list[ThreadSummaryResponse]:
    return [
        ThreadSummaryResponse(
            thread_id=conversation.thread_id,
            title=conversation.title,
            message_count=conversation.message_count,
            updated_at=conversation.updated_at,
            pinned=conversation.pinned,
            project_id=conversation.project_id,
            preview=conversation.preview,
        )
        for conversation in agent_service.list_conversations()
    ]


@router.get("/threads/{thread_id}", response_model=ThreadResponse)
def get_thread(
    thread_id: Annotated[str, Path(min_length=1)],
    agent_service: AgentServiceDependency,
) -> ThreadResponse:
    conversation = agent_service.get_conversation(thread_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    return ThreadResponse(
        thread_id=conversation.thread_id,
        title=conversation.title,
        message_count=conversation.message_count,
        updated_at=conversation.updated_at,
        pinned=conversation.pinned,
        project_id=conversation.project_id,
        preview=conversation.preview,
        messages=[
            ThreadMessageResponse(
                role=message.role,
                content=message.content,
                tool_calls=message.tool_calls,
                a2ui_messages=message.a2ui_messages,
                attachments=message.attachments,
            )
            for message in conversation.messages
        ],
        pending_hypothesis_review=conversation.pending_hypothesis_review,
        pending_technical_plan_review=conversation.pending_technical_plan_review,
        completed_reviews=conversation.completed_reviews,
    )


@router.patch("/threads/{thread_id}", response_model=ThreadSummaryResponse)
def update_thread(
    thread_id: Annotated[str, Path(min_length=1)],
    payload: ThreadUpdateRequest,
    agent_service: AgentServiceDependency,
) -> ThreadSummaryResponse:
    conversation = agent_service.update_conversation(
        thread_id,
        title=payload.title,
        pinned=payload.pinned,
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return ThreadSummaryResponse(
        thread_id=conversation.thread_id,
        title=conversation.title,
        message_count=conversation.message_count,
        updated_at=conversation.updated_at,
        pinned=conversation.pinned,
        project_id=conversation.project_id,
        preview=conversation.preview,
    )


@router.patch("/threads/{thread_id}/project", response_model=ThreadSummaryResponse)
def set_thread_project(
    thread_id: Annotated[str, Path(min_length=1)],
    payload: ThreadProjectRequest,
    agent_service: AgentServiceDependency,
) -> ThreadSummaryResponse:
    try:
        conversation = agent_service.set_conversation_project(
            thread_id,
            payload.project_id,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return ThreadSummaryResponse(
        thread_id=conversation.thread_id,
        title=conversation.title,
        message_count=conversation.message_count,
        updated_at=conversation.updated_at,
        pinned=conversation.pinned,
        project_id=conversation.project_id,
        preview=conversation.preview,
    )


@router.delete("/threads/{thread_id}", status_code=204)
def delete_thread(
    thread_id: Annotated[str, Path(min_length=1)],
    agent_service: AgentServiceDependency,
) -> Response:
    if not agent_service.delete_conversation(thread_id):
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return Response(status_code=204)


__all__ = ["router"]
