"""Chat HTTP controller."""

import logging
from collections.abc import Iterator
from typing import Annotated

from agent_stream_py import agent_event_data, error_event
from fastapi import APIRouter, HTTPException, Path
from fastapi.sse import EventSourceResponse, ServerSentEvent

from archwise_agent.backend.data import (
    ChatCancelResponse,
    ChatRequest,
    ChatResponse,
)
from archwise_agent.backend.dependencies import AgentServiceDependency
from archwise_agent.core import AgentCancelledError, ConcurrentRunError
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
            run_id=payload.run_id,
        )
    except (AgentCancelledError, ConcurrentRunError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
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
            run_id=payload.run_id,
        ):
            yield _to_server_sent_event(event)
    except (ValueError, ConcurrentRunError) as error:
        yield _error_server_sent_event(
            thread_id=payload.thread_id,
            run_id=payload.run_id or "unknown",
            message=str(error),
        )
    except Exception:
        logger.exception("ArchWise agent stream failed")
        yield _error_server_sent_event(
            thread_id=payload.thread_id,
            run_id=payload.run_id or "unknown",
            message="Agent execution failed.",
        )


@router.post(
    "/chat/runs/{run_id}/cancel",
    response_model=ChatCancelResponse,
)
def cancel_chat_run(
    run_id: Annotated[str, Path(min_length=1)],
    agent_service: AgentServiceDependency,
) -> ChatCancelResponse:
    """Request cooperative cancellation for one active agent run."""

    try:
        cancelled = agent_service.cancel_run(run_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return ChatCancelResponse(run_id=run_id, cancelled=cancelled)


def _to_server_sent_event(event: AgentStreamEvent) -> ServerSentEvent:
    return ServerSentEvent(
        event="archwise",
        data=agent_event_data(event),
    )


def _error_server_sent_event(
    *, thread_id: str, run_id: str, message: str
) -> ServerSentEvent:
    return ServerSentEvent(
        event="archwise",
        data=agent_event_data(
            error_event(
                thread_id=thread_id,
                run_id=run_id,
                message=message,
            )
        ),
    )


__all__ = ["router"]
