"""FastAPI dependencies for the local chat service."""

from typing import Annotated

from fastapi import Depends, Request

from archhypo_flow_agent.services import AgentService


def get_agent_service(request: Request) -> AgentService:
    return request.app.state.agent_service


AgentServiceDependency = Annotated[AgentService, Depends(get_agent_service)]

__all__ = ["AgentServiceDependency", "get_agent_service"]
