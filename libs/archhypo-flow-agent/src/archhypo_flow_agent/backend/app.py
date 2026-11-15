"""FastAPI application for the local ArchHypo Flow chat runtime."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from archhypo_flow_agent.backend.controllers import (
    artifacts_router,
    chat_router,
    health_router,
    projects_router,
    threads_router,
)
from archhypo_flow_agent.backend.controllers.skills import router as skills_router
from archhypo_flow_agent.config import settings
from archhypo_flow_agent.providers import (
    create_openrouter_model,
    create_system_one_client,
)
from archhypo_flow_agent.services import AgentService


def create_app(agent_service: AgentService | None = None) -> FastAPI:
    """Create the API with an optional service instance for tests."""

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
        owns_service = agent_service is None
        if agent_service is None:
            try:
                system_one_client = create_system_one_client(settings)
                application.state.agent_service = AgentService(
                    model=create_openrouter_model(),
                    system_one_client=system_one_client,
                )
                application.state.chat_configuration_error = None
            except ValueError as error:
                application.state.agent_service = AgentService()
                application.state.chat_configuration_error = str(error)
        else:
            application.state.agent_service = agent_service
            application.state.chat_configuration_error = (
                None
                if agent_service.chat_ready
                else (
                    "Configure OPENROUTER_API_KEY and SYSTEM_ONE_MODEL in "
                    "libs/archhypo-flow-agent/.env."
                )
            )
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
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type"],
    )
    application.include_router(skills_router)
    application.include_router(health_router)
    application.include_router(artifacts_router)
    application.include_router(chat_router)
    application.include_router(projects_router)
    application.include_router(threads_router)
    return application


app = create_app()

__all__ = ["app", "create_app"]
