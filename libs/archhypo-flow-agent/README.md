# archhypo-flow-agent

Minimal conversational agent harness for ArchHypo Flow. The initial graph wraps a LangChain ReAct agent in one `response_generation` node; the model and tools are injected so provider configuration and future dynamic skills remain outside graph construction.

## Structure

```text
src/archhypo_flow_agent/
├── agents/          # ReAct agent assembly
├── backend/         # Local FastAPI chat and conversation-history API
├── cli/             # Graph utilities
├── config/          # Environment-backed settings
├── core/            # Shared graph state and contracts
├── graph/           # LangGraph workflow
├── observability/   # Optional tracing integrations
├── persistence/     # Checkpoint and conversation persistence
├── providers/       # LLM provider factories
├── services/        # Application-facing agent operations
├── stream/          # Validated events shared with the frontend
└── tools/           # Agent tools, including future skill access
```

## Development

```bash
cd libs/archhypo-flow-agent
uv sync --dev
uv run pytest
uv run ruff check .
```

The local API exposes `POST /api/chat`, `GET /api/threads`, and `GET /api/threads/{thread_id}`. LangGraph checkpoints and conversation metadata share one SQLite database, defaulting to `~/.local/share/archhypo-flow/runtime/checkpoints.sqlite`; override the storage root with `ARCHHYPO_FLOW_STORAGE_ROOT`.

The desktop API uses `ChatOpenRouter` from the configured provider factory. Set `OPENROUTER_API_KEY` and optionally `OPENROUTER_MODEL` in this package's `.env`; the development launcher starts the backend with this directory as its working directory. Without a key, conversation history remains available, but chat requests return a configuration error instead of a fake reply.

## Draw the graph

From the repository root:

```bash
uv run --project libs/archhypo-flow-agent archhypo-flow-workflow-diagram
```

This writes the Mermaid graph to `docs/architecture/archhypo-flow-agent.mmd`. Override the output directory with `--output-directory`.
