"""FastAPI dependencies for backend routes."""

from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request

from archwise_agent.services import AgentService


def get_agent_service(request: Request) -> AgentService:
    """Resolve the long-lived service created by the application lifespan."""

    service: Any = getattr(request.app.state, "agent_service", None)
    if service is None:
        raise HTTPException(
            status_code=503,
            detail="The ArchWise agent is not ready.",
        )
    return service


AgentServiceDependency = Annotated[AgentService, Depends(get_agent_service)]

__all__ = ["AgentServiceDependency", "get_agent_service"]
