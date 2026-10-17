"""Chat HTTP controller."""

import logging
from collections.abc import Iterator
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent

from archhypo_flow_agent.backend.dependencies import AgentServiceDependency
from archhypo_flow_agent.core import ChatRequest, ChatResponse
from archhypo_flow_agent.providers import SystemOneError
from archhypo_flow_agent.services.chat_execution import ReviewStateError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])
_ROUTING_ERROR_MESSAGE = (
    "SystemOne request routing failed. Check SYSTEM_ONE_MODEL, the decision "
    "endpoint, and provider availability. No alternative router was used."
)


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
            detail=request.app.state.chat_configuration_error,
        )

    try:
        return agent_service.respond(payload)
    except ReviewStateError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except SystemOneError as error:
        logger.error("SystemOne routing failed (%s)", type(error).__name__)
        raise HTTPException(status_code=502, detail=_ROUTING_ERROR_MESSAGE) from error
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
            detail=request.app.state.chat_configuration_error,
        )

    run_id = uuid4().hex

    def events() -> Iterator[ServerSentEvent]:
        try:
            for event in agent_service.stream(payload, run_id=run_id):
                yield ServerSentEvent(event="chat", data=event)
        except ReviewStateError as error:
            yield ServerSentEvent(
                event="chat",
                data=_stream_error_data(run_id, payload.thread_id, str(error)),
            )
        except LookupError as error:
            yield ServerSentEvent(
                event="chat",
                data=_stream_error_data(run_id, payload.thread_id, str(error)),
            )
        except SystemOneError as error:
            logger.error("SystemOne routing failed (%s)", type(error).__name__)
            yield ServerSentEvent(
                event="chat",
                data=_stream_error_data(
                    run_id, payload.thread_id, _ROUTING_ERROR_MESSAGE
                ),
            )
        except Exception as error:
            logger.error("Chat stream failed (%s)", type(error).__name__)
            yield ServerSentEvent(
                event="chat",
                data=_stream_error_data(
                    run_id,
                    payload.thread_id,
                    "The OpenRouter request failed. Check the API key, model, "
                    "and provider limits.",
                ),
            )

    return events()


def _stream_error_data(run_id: str, thread_id: str, message: str) -> dict[str, object]:
    return {
        "protocol_version": 1,
        "run_id": run_id,
        "thread_id": thread_id,
        "type": "error",
        "message": message,
    }


__all__ = ["router"]
