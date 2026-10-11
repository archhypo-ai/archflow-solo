"""Chat HTTP controller."""

import logging

from fastapi import APIRouter, HTTPException, Request

from archhypo_flow_agent.backend.dependencies import AgentServiceDependency
from archhypo_flow_agent.core import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def send_message(
    payload: ChatRequest,
    request: Request,
    agent_service: AgentServiceDependency,
) -> ChatResponse:
    """Run one OpenRouter chat turn and persist it in SQLite."""

    if request.app.state.chat_configuration_error is not None:
        raise HTTPException(
            status_code=503,
            detail="Configure OPENROUTER_API_KEY in libs/archhypo-flow-agent/.env.",
        )

    try:
        return agent_service.respond(payload)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        logger.error("Chat generation failed (%s)", type(error).__name__)
        raise HTTPException(
            status_code=502,
            detail=(
                "The OpenRouter request failed. Check the API key, model, "
                "and provider limits."
            ),
        ) from error


__all__ = ["router"]
