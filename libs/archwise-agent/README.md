# archwise-agent

The first ArchWise agent core. This version contains only a generic
conversational agent built with LangGraph and OpenRouter.

## Package structure

```text
src/archwise_agent/
├── config/       # Pydantic environment-backed settings
├── core/         # State, execution context, and agent contracts
├── persistence/  # SQLite checkpoints, repositories, migrations, and paths
├── providers/    # Model provider integrations
├── agents/       # Orchestrator and concrete agents
│   ├── orchestrator/
│   └── subagents/ # Added as workflows are introduced
├── services/     # Application API for future interfaces
└── backend/      # Minimal HTTP adapter for local clients
```

Each package exposes its public API through `__init__.py`. Applications should
consume `archwise_agent` or its public subpackages rather than internal modules.

Tests mirror the source layout:

```text
tests/
├── agents/orchestrator/
└── backend/controllers/
```

## Configuration

```bash
export OPENROUTER_API_KEY="..."
export OPENROUTER_MODEL="openrouter:deepseek/deepseek-v4.1-flash"
```

The default model is already
`openrouter:deepseek/deepseek-v4.1-flash`. The prefix is accepted in the
configuration and removed only before the request is sent to OpenRouter.

## Development

```bash
cd libs/archwise-agent
uv sync --dev
uv run pytest
```

The backend uses a SQLite checkpointer at
`.archhypo/runtime/checkpoints.sqlite` in the monorepo root. The directory is
created on first startup and is ignored by Git. Database migrations run before
LangGraph initializes its checkpoint tables. Set `ARCHWISE_STORAGE_ROOT` to
use another storage directory.

`build_archwise_agent` still accepts an injected checkpointer, which keeps unit
tests and alternative runtimes independent from the local database. The
application-facing `AgentService` opens and owns the SQLite connection by
default.

## Local backend

```bash
cd libs/archwise-agent
uv sync --dev
uv run fastapi dev --host 127.0.0.1 --port 8765
```

The backend version is sourced from the package version in `pyproject.toml`.
The backend listens on `http://127.0.0.1:8765` by default. The executable
server entrypoint remains available with
`uv run python -m archwise_agent.backend.server`.

```bash
curl http://127.0.0.1:8765/api/health

curl -X POST http://127.0.0.1:8765/api/chat \\
  -H 'Content-Type: application/json' \\
  -d '{"thread_id":"curl-test","message":"Explain ArchHypo briefly."}'

curl -N -X POST http://127.0.0.1:8765/api/chat/stream \\
  -H 'Accept: text/event-stream' \\
  -H 'Content-Type: application/json' \\
  -d '{"thread_id":"curl-stream-test","message":"Explain ArchHypo briefly."}'
```

The backend creates one long-lived agent service and uses the supplied
`thread_id` for persistent conversation checkpoints. The `/api/chat/stream`
endpoint uses standard SSE events (`phase`, `delta`, `done`, `cancelled`, and
`error`) for clients that need progressive responses. Active runs can receive a
cooperative cancellation request through
`POST /api/chat/runs/{run_id}/cancel`. User-facing conversation
metadata is kept in the same database catalog, while the transcript and graph
state remain owned by LangGraph's checkpoint tables. Execution context already
has contracts for `thread_id`, `workspace_id`, `project_id`, `user_id`, and
`run_id`; workspace metadata will be persisted in a later schema version.
