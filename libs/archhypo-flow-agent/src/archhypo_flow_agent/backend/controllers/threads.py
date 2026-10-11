"""Conversation history HTTP controller."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from archhypo_flow_agent.backend.dependencies import AgentServiceDependency
from archhypo_flow_agent.backend.schemas import (
    ThreadMessageResponse,
    ThreadResponse,
    ThreadSummaryResponse,
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
        messages=[
            ThreadMessageResponse(role=message.role, content=message.content)
            for message in conversation.messages
        ],
    )


__all__ = ["router"]
