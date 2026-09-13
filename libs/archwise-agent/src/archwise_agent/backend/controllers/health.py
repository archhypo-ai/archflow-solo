"""Health HTTP controller."""

from fastapi import APIRouter

from archwise_agent.backend.data import BACKEND_API_VERSION, HealthResponse
from archwise_agent.backend.dependencies import AgentServiceDependency

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(agent_service: AgentServiceDependency) -> HealthResponse:
    """Report whether the long-lived agent service is available."""

    return HealthResponse(
        status="ok",
        agent_ready=agent_service is not None,
        api_version=BACKEND_API_VERSION,
        sse_chat=True,
    )


__all__ = ["router"]
