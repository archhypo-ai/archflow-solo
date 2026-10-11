"""FastAPI application for the local ArchHypo Flow chat runtime."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from archhypo_flow_agent.backend.controllers import (
    chat_router,
    health_router,
    threads_router,
)
from archhypo_flow_agent.providers.openrouter import create_openrouter_model
from archhypo_flow_agent.services import AgentService


def create_app(agent_service: AgentService | None = None) -> FastAPI:
    """Create the API with an optional service instance for tests."""

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
        owns_service = agent_service is None
        if agent_service is None:
            try:
                application.state.agent_service = AgentService(
                    model=create_openrouter_model()
                )
                application.state.chat_configuration_error = None
            except ValueError as error:
                application.state.agent_service = AgentService()
                application.state.chat_configuration_error = str(error)
        else:
            application.state.agent_service = agent_service
            application.state.chat_configuration_error = None
        try:
            yield
        finally:
            if owns_service:
                application.state.agent_service.close()

    application = FastAPI(
        title="ArchHypo Flow Local API",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:1420",
            "http://localhost:1420",
            "tauri://localhost",
            "http://tauri.localhost",
        ],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type"],
    )
    application.include_router(health_router)
    application.include_router(chat_router)
    application.include_router(threads_router)
    return application


app = create_app()

__all__ = ["app", "create_app"]
