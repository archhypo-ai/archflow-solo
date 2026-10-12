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
└── tools/           # Agent tools such as bounded public-web search
```

## Development

```bash
cd libs/archhypo-flow-agent
uv sync --dev
uv run pytest
uv run ruff check .
```

The local API exposes `POST /api/chat`, the streaming `POST /api/chat/stream` endpoint used by the desktop UI, `GET /api/threads`, and `GET /api/threads/{thread_id}`. The streaming endpoint sends tool-call starts and results as they occur before the final reply. LangGraph checkpoints and conversation metadata share one SQLite database, defaulting to `~/.local/share/archhypo-flow/runtime/checkpoints.sqlite`; override the storage root with `ARCHHYPO_FLOW_STORAGE_ROOT`.

The desktop API uses `ChatOpenRouter` from the configured provider factory. Set `OPENROUTER_API_KEY` and optionally `OPENROUTER_MODEL` in this package's `.env`; the development launcher starts the backend with this directory as its working directory. Without a key, conversation history remains available, but chat requests return a configuration error instead of a fake reply.

Global context is saved in the Tauri Store preferences file and sent as a snapshot with each chat request. Project context remains in the project's SQLite `instructions` field and is resolved through the conversation's persisted project association. The shared `agents.prompts.build_system_prompt()` function appends both contexts to the fixed prompt without storing them in checkpointed conversation messages; project context is included only for conversations belonging to that project.

Tavily public-web search is enabled when `TAVILY_API_KEY` is configured. Install its optional dependency with `uv sync --extra research` (the desktop development launcher includes this extra). The tool only accepts bounded public queries, rejects obvious secrets and local paths, and returns short excerpts rather than raw page content. Never include private code, project details, credentials, or secrets in a search query.

## Draw the graph

From the repository root:

```bash
uv run --project libs/archhypo-flow-agent archhypo-flow-workflow-diagram
```

This writes the Mermaid graph to `docs/architecture/archhypo-flow-agent.mmd`. Override the output directory with `--output-directory`.
