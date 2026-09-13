"""Chat HTTP controller."""

from fastapi import APIRouter, HTTPException

from archwise_agent.backend.data import ChatRequest, ChatResponse
from archwise_agent.backend.dependencies import AgentServiceDependency

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
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return ChatResponse(
        thread_id=turn.thread_id,
        message=turn.text,
    )


__all__ = ["router"]
