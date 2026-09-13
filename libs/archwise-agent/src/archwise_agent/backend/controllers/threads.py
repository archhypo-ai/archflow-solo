"""Conversation HTTP controller."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Response

from archwise_agent.backend.data import (
    ThreadMessageResponse,
    ThreadResponse,
    ThreadSummaryResponse,
    ThreadUpdateRequest,
)
from archwise_agent.backend.dependencies import AgentServiceDependency
from archwise_agent.services import ConversationSummary

router = APIRouter(prefix="/api", tags=["threads"])


def _summary_response(conversation: ConversationSummary) -> ThreadSummaryResponse:
    return ThreadSummaryResponse(
        thread_id=conversation.thread_id,
        title=conversation.title,
        message_count=conversation.message_count,
        pinned=conversation.pinned,
    )


@router.get("/threads", response_model=list[ThreadSummaryResponse])
def list_threads(
    agent_service: AgentServiceDependency,
) -> list[ThreadSummaryResponse]:
    """List conversations available in the active agent runtime."""

    return [
        _summary_response(conversation)
        for conversation in agent_service.list_conversations()
    ]


@router.get("/threads/{thread_id}", response_model=ThreadResponse)
def get_thread(
    thread_id: Annotated[str, Path(min_length=1)],
    agent_service: AgentServiceDependency,
) -> ThreadResponse:
    """Return one conversation transcript for client-side switching."""

    try:
        conversation = agent_service.get_conversation(thread_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if conversation is None:
        raise HTTPException(status_code=404, detail="Thread not found.")

    return ThreadResponse(
        thread_id=conversation.thread_id,
        title=conversation.title,
        message_count=conversation.message_count,
        messages=[
            ThreadMessageResponse(role=message.role, content=message.content)
            for message in conversation.messages
        ],
        pinned=conversation.pinned,
    )


@router.patch("/threads/{thread_id}", response_model=ThreadSummaryResponse)
def update_thread(
    thread_id: Annotated[str, Path(min_length=1)],
    payload: ThreadUpdateRequest,
    agent_service: AgentServiceDependency,
) -> ThreadSummaryResponse:
    """Update mutable conversation metadata such as its pinned state."""

    try:
        conversation = agent_service.update_conversation(
            thread_id,
            title=payload.title,
            pinned=payload.pinned,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if conversation is None:
        raise HTTPException(status_code=404, detail="Thread not found.")

    return _summary_response(conversation)


@router.delete("/threads/{thread_id}", status_code=204)
def delete_thread(
    thread_id: Annotated[str, Path(min_length=1)],
    agent_service: AgentServiceDependency,
) -> Response:
    """Delete one conversation from the checkpoint and metadata stores."""

    try:
        deleted = agent_service.delete_conversation(thread_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if not deleted:
        raise HTTPException(status_code=404, detail="Thread not found.")

    return Response(status_code=204)


__all__ = ["router"]
