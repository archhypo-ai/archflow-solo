"""Health endpoint for the local agent API."""

from fastapi import APIRouter, Request

from archhypo_flow_agent.backend.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    configuration_error = request.app.state.chat_configuration_error
    return HealthResponse(
        agent_ready=configuration_error is None,
        configuration_error=configuration_error,
    )


__all__ = ["router"]
