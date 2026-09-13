"""Chat HTTP controller."""

import logging
from collections.abc import Iterator

from fastapi import APIRouter, HTTPException
from fastapi.sse import EventSourceResponse, ServerSentEvent

from archwise_agent.backend.data import ChatRequest, ChatResponse
from archwise_agent.backend.dependencies import AgentServiceDependency
from archwise_agent.services import AgentStreamEvent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    agent_service: AgentServiceDependency,
) -> ChatResponse:
    """Execute one message against the requested checkpoint thread."""

    try:
        turn = agent_service.send(
            thread_id=payload.thread_id,
            message=payload.message,
            workspace_id=payload.workspace_id,
            project_id=payload.project_id,
            user_id=payload.user_id,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return ChatResponse(
        thread_id=turn.thread_id,
        message=turn.text,
    )


@router.post("/chat/stream", response_class=EventSourceResponse)
def chat_stream(
    payload: ChatRequest,
    agent_service: AgentServiceDependency,
) -> Iterator[ServerSentEvent]:
    """Stream one agent turn using standard Server-Sent Events."""

    try:
        for event in agent_service.stream(
            thread_id=payload.thread_id,
            message=payload.message,
            workspace_id=payload.workspace_id,
            project_id=payload.project_id,
            user_id=payload.user_id,
        ):
            yield _to_server_sent_event(event)
    except ValueError as error:
        yield ServerSentEvent(
            event="error",
            data={
                "thread_id": payload.thread_id,
                "message": str(error),
            },
        )
    except Exception:
        logger.exception("ArchWise agent stream failed")
        yield ServerSentEvent(
            event="error",
            data={
                "thread_id": payload.thread_id,
                "message": "Agent execution failed.",
            },
        )


def _to_server_sent_event(event: AgentStreamEvent) -> ServerSentEvent:
    data: dict[str, str] = {"thread_id": event.thread_id}
    if event.phase is not None:
        data["phase"] = event.phase
    if event.text is not None:
        data["text"] = event.text

    return ServerSentEvent(event=event.kind, data=data)


__all__ = ["router"]
