"""FastAPI application for the ArchWise agent."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from archwise_agent.services import AgentService

from .controllers import chat_router, health_router


def _create_lifespan(
    agent_service: AgentService | None,
):
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        app.state.agent_service = (
            agent_service if agent_service is not None else AgentService()
        )
        yield

    return lifespan


def create_app(agent_service: AgentService | None = None) -> FastAPI:
    """Create the HTTP application with an injectable agent service."""

    application = FastAPI(
        title="ArchWise Agent Backend",
        version="0.1.0",
        lifespan=_create_lifespan(agent_service),
    )
    application.include_router(health_router)
    application.include_router(chat_router)
    return application


app = create_app()

__all__ = ["app", "create_app"]
