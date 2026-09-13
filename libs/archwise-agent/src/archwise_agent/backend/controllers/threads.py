"""Conversation HTTP controller."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from archwise_agent.backend.data import (
    ThreadMessageResponse,
    ThreadResponse,
    ThreadSummaryResponse,
)
from archwise_agent.backend.dependencies import AgentServiceDependency

router = APIRouter(prefix="/api", tags=["threads"])


@router.get("/threads", response_model=list[ThreadSummaryResponse])
def list_threads(
    agent_service: AgentServiceDependency,
) -> list[ThreadSummaryResponse]:
    """List conversations available in the active agent runtime."""

    return [
        ThreadSummaryResponse(
            thread_id=conversation.thread_id,
            title=conversation.title,
            message_count=conversation.message_count,
        )
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
    )


__all__ = ["router"]
