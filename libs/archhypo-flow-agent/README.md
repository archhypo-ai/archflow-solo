# archhypo-flow-agent

Minimal conversational agent harness for ArchHypo Flow. The initial graph wraps a LangChain ReAct agent in one `response_generation` node; the model and tools are injected so provider configuration and future dynamic skills remain outside graph construction.

## Structure

```text
src/archhypo_flow_agent/
├── agents/          # ReAct agent assembly
├── backend/         # Local HTTP adapter (next increment)
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

Set `OPENROUTER_API_KEY` to use the configured provider. A sample environment file is available as `.env.example`.

## Draw the graph

From the repository root:

```bash
uv run --project libs/archhypo-flow-agent archhypo-flow-workflow-diagram
```

This writes the Mermaid graph to `docs/architecture/archhypo-flow-agent.mmd`. Override the output directory with `--output-directory`.
