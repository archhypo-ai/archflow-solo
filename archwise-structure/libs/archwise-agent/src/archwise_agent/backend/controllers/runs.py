"""Run-status HTTP controller."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from archwise_agent.backend.data import ActiveRunResponse
from archwise_agent.backend.dependencies import AgentServiceDependency

router = APIRouter(prefix="/api", tags=["runs"])


@router.get(
    "/threads/{thread_id}/runs/active",
    response_model=ActiveRunResponse | None,
)
def get_active_run(
    thread_id: Annotated[str, Path(min_length=1)],
    agent_service: AgentServiceDependency,
) -> ActiveRunResponse | None:
    """Return the run currently executing for a conversation, if any."""

    try:
        run = agent_service.get_active_run(thread_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if run is None:
        return None
    return ActiveRunResponse(
        thread_id=run.thread_id,
        run_id=run.run_id,
        status=run.status,
    )


__all__ = ["router"]
