"""FastAPI application for the local ArchHypo Flow chat runtime."""

import logging
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
from archhypo_flow_agent.backend.controllers.mcps import router as mcps_router
from archhypo_flow_agent.backend.controllers.providers import router as providers_router
from archhypo_flow_agent.backend.controllers.skills import router as skills_router
from archhypo_flow_agent.backend.controllers.tool_catalog import (
    router as tool_catalog_router,
)
from archhypo_flow_agent.config.provider_config import effective_provider_settings
from archhypo_flow_agent.providers import (
    create_openrouter_model,
    create_system_one_client,
)
from archhypo_flow_agent.services import AgentService
from archhypo_flow_agent.services.mcp_manager import MCPManager

logger = logging.getLogger(__name__)


def create_app(agent_service: AgentService | None = None) -> FastAPI:
    """Create the API with an optional service instance for tests."""

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
        owns_service = agent_service is None
        if agent_service is None:
            try:
                configuration = effective_provider_settings()
                system_one_client = create_system_one_client(configuration)
                application.state.agent_service = AgentService(
                    model=create_openrouter_model(configuration),
                    system_one_client=system_one_client,
                    chat_model_id=configuration.openrouter_model,
                    system_one_model_id=configuration.system_one_model,
                    configuration=configuration,
                )
                application.state.chat_configuration_error = None
            except (OSError, ValueError) as error:
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
            try:
                await application.state.mcp_manager.connect_on_startup()
            except ValueError as error:
                logger.warning("Could not load MCP configuration: %s", error)
            yield
        finally:
            await application.state.mcp_manager.close()
            if owns_service:
                application.state.agent_service.close()

    application = FastAPI(
        title="ArchHypo Flow Local API",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.state.mcp_manager = MCPManager()
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
        expose_headers=["X-Model-Cache"],
    )
    application.include_router(providers_router)
    application.include_router(tool_catalog_router)
    application.include_router(mcps_router)
    application.include_router(skills_router)
    application.include_router(health_router)
    application.include_router(artifacts_router)
    application.include_router(chat_router)
    application.include_router(projects_router)
    application.include_router(threads_router)
    return application


app = create_app()

__all__ = ["app", "create_app"]
