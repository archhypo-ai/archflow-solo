"""Chat HTTP controller."""

import logging
from collections.abc import Iterator

from fastapi import APIRouter, HTTPException, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent

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


@router.post(
    "/chat/stream",
    response_class=EventSourceResponse,
    response_model=None,
)
def stream_message(
    payload: ChatRequest,
    request: Request,
    agent_service: AgentServiceDependency,
) -> Iterator[ServerSentEvent]:
    """Stream tool progress and the completed reply as server-sent events."""

    if request.app.state.chat_configuration_error is not None:
        raise HTTPException(
            status_code=503,
            detail="Configure OPENROUTER_API_KEY in libs/archhypo-flow-agent/.env.",
        )

    def events() -> Iterator[ServerSentEvent]:
        try:
            for event in agent_service.stream(payload):
                yield ServerSentEvent(event="chat", data=event)
        except LookupError as error:
            yield ServerSentEvent(
                event="chat",
                data={"type": "error", "message": str(error)},
            )
        except Exception as error:
            logger.error("Chat stream failed (%s)", type(error).__name__)
            yield ServerSentEvent(
                event="chat",
                data={
                    "type": "error",
                    "message": (
                        "The OpenRouter request failed. Check the API key, model, "
                        "and provider limits."
                    ),
                },
            )

    return events()


__all__ = ["router"]
