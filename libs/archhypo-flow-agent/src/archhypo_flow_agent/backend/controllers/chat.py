"""Chat HTTP controller."""

import logging

from fastapi import APIRouter, HTTPException, Request

from archhypo_flow_agent.backend.dependencies import AgentServiceDependency
from archhypo_flow_agent.core import ChatRequest, ChatResponse, StructuredOutputError
from archhypo_flow_agent.persistence import ArtifactPersistenceError
from archhypo_flow_agent.providers import SystemOneError
from archhypo_flow_agent.services import AgentService, ChatNotConfiguredError
from archhypo_flow_agent.services.chat_execution import ReviewStateError
from archhypo_flow_agent.services.document_extraction import DocumentExtractionError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])
_ROUTING_ERROR_MESSAGE = (
    "SystemOne request routing failed. Check SYSTEM_ONE_MODEL, the decision "
    "endpoint, and provider availability. No alternative router was used."
)


def _configuration_error(request: Request, service: AgentService) -> str | None:
    if service.dynamic_provider_settings:
        return service.runtime_configuration_error()
    return request.app.state.chat_configuration_error


@router.post("/chat", response_model=ChatResponse)
def send_message(
    payload: ChatRequest,
    request: Request,
    agent_service: AgentServiceDependency,
) -> ChatResponse:
    """Run one OpenRouter chat turn and persist it in SQLite."""

    configuration_error = _configuration_error(request, agent_service)
    if configuration_error is not None:
        raise HTTPException(status_code=503, detail=configuration_error)

    try:
        return agent_service.respond(payload)
    except ChatNotConfiguredError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except DocumentExtractionError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except ReviewStateError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except SystemOneError as error:
        logger.error("SystemOne routing failed (%s)", type(error).__name__)
        raise HTTPException(status_code=502, detail=_ROUTING_ERROR_MESSAGE) from error
    except StructuredOutputError as error:
        logger.error("Structured model output failed in stage %s", error.stage)
        raise HTTPException(
            status_code=502,
            detail=_structured_output_error_message(error),
        ) from error
    except ArtifactPersistenceError as error:
        logger.error("ArchHypo artifact persistence failed")
        raise HTTPException(
            status_code=503,
            detail=_artifact_persistence_error_message(),
        ) from error
    except Exception as error:
        logger.error("Chat generation failed (%s)", type(error).__name__)
        raise HTTPException(
            status_code=502,
            detail=(
                "The OpenRouter request failed. Check the API key, model, "
                "and provider limits."
            ),
        ) from error


def _structured_output_error_message(error: StructuredOutputError) -> str:
    if error.stage == "hypothesis_assessment":
        return (
            "The model returned an incomplete assessment after one correction "
            "attempt. The pending workflow state was preserved; retry the turn."
        )
    return (
        "The model returned invalid structured output after a correction attempt. "
        "The pending workflow state was preserved; retry the turn."
    )


def _artifact_persistence_error_message() -> str:
    return (
        "The ArchHypo result was generated but could not be saved. "
        "The conversation state was preserved; retry the turn."
    )


__all__ = ["router"]
