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
└── services/     # Application API for future interfaces
```

Each package exposes its public API through `__init__.py`. Applications should
consume `archwise_agent` or its public subpackages rather than internal modules.

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
