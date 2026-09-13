# archwise-agent

The first ArchWise agent core. This version contains only a generic
conversational agent built with LangGraph and OpenRouter.

## Package structure

```text
src/archwise_agent/
├── config/       # Pydantic environment-backed settings
├── core/         # Shared state contracts
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

The agent uses `InMemorySaver` by default. The checkpointer is injectable in
`build_archwise_agent` and `AgentService`, allowing a future SQLite
implementation without changing the state contract or interface adapters.

## Local backend

```bash
cd libs/archwise-agent
uv sync --dev
uv run fastapi dev --host 127.0.0.1 --port 8765
```

The backend listens on `http://127.0.0.1:8765` by default. The executable
server entrypoint remains available with
`uv run python -m archwise_agent.backend.server`.

```bash
curl http://127.0.0.1:8765/api/health

curl -X POST http://127.0.0.1:8765/api/chat \\
  -H 'Content-Type: application/json' \\
  -d '{"thread_id":"curl-test","message":"Explain ArchHypo briefly."}'
```

The backend creates one long-lived agent service and uses the supplied
`thread_id` for in-memory conversation checkpoints. Conversations are lost
when the process stops until a persistent checkpointer is introduced.
