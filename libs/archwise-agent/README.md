# archwise-agent

The ArchWise workflow transforms one architectural uncertainty into a
structured hypothesis, classification, and technical plan using LangGraph and
OpenRouter.

## Package structure

```text
skills/             # Progressive-disclosure domain skills
└── archhypo-catalog/
src/archwise_agent/
├── config/          # Pydantic environment-backed settings
├── core/            # State, Pydantic domain models, and execution context
├── persistence/     # SQLite checkpoints, repositories, migrations, and paths
├── providers/       # Model provider integrations
├── agents/          # Orchestrator and concrete workflow agents
│   ├── hypothesis_assessor/
│   ├── hypothesis_formulator/
│   ├── orchestrator/
│   │   └── nodes/
│   ├── request_router/
│   ├── response_composer/
│   └── technical_planner/
├── cli/             # Package command-line utilities
├── observability/   # Optional LangSmith/Langfuse tracing
├── services/        # Application API for future interfaces
└── backend/         # Minimal HTTP adapter for local clients
```

Each package exposes its public API through `__init__.py`. Applications should
consume `archwise_agent` or its public subpackages rather than internal modules.

Tests mirror the source layout:

```text
tests/
├── agents/hypothesis_formulator/
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

Jev routing is optional and disabled by default. It uses the same OpenRouter
API key through the Decisions API:

```bash
export JEV_ENABLED=true
export JEV_MODEL="typesafe/jev-1.13"
```

If the Jev request fails or returns an invalid route, the existing LLM router
is used as a fallback.

The technical planner uses the `archhypo-catalog` skill through
`SkillsMiddleware` and read-only `FilesystemMiddleware`. It loads the skill
metadata first and reads the relevant pattern references only when needed.

The optional `tavily_search` tool is available for future research-oriented
agents. It is not attached to the current workflow yet. Install it with:

```bash
uv sync --extra research
```

Set `TAVILY_API_KEY` to enable it. The tool performs bounded public-web
searches, omits raw page content, rejects obvious private data and local paths,
and returns source URLs for citation. Its usage policy is exported as
`TAVILY_RESEARCH_PROMPT_SNIPPET` for the future Codebase Investigator.

## Optional observability

Tracing is disabled by default. LangSmith can be enabled with its standard
variables, while Langfuse requires the optional dependency group:

```bash
cd libs/archwise-agent
uv sync --dev --extra observability
```

```bash
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=archwise

LANGFUSE_ENABLED=true
LANGFUSE_SECRET_KEY=...
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

The `AgentService` propagates tracing callbacks and metadata for each
LangGraph execution, including `thread_id`, `workspace_id`, `project_id`,
`user_id`, and `run_id`. Provider failures do not stop the agent execution.
Review data retention and masking before enabling tracing with sensitive
conversation content.

## Development

```bash
cd libs/archwise-agent
uv sync --dev
uv run pytest
```

### Generate the workflow diagram

From the repository root, generate the current LangGraph workflow as Mermaid
source and PNG:

```bash
uv run --project libs/archwise-agent archwise-workflow-diagram
```

The files are written to:

```text
docs/architecture/archwise-workflow.mmd
docs/architecture/archwise-workflow.png
```

Use `--output-directory` to write them elsewhere:

```bash
uv run --project libs/archwise-agent archwise-workflow-diagram \
  --output-directory /tmp/archwise-diagram
```

The diagram is generated from the compiled graph without making an LLM request.

The backend uses a SQLite checkpointer at
`.archhypo/runtime/checkpoints.sqlite` in the monorepo root. The directory is
created on first startup and is ignored by Git. Database migrations run before
LangGraph initializes its checkpoint tables. Set `ARCHWISE_STORAGE_ROOT` to
use another storage directory.

`build_orchestrator_agent` still accepts an injected checkpointer, which keeps unit
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
endpoint uses the shared agent stream protocol (`phase`, `text_delta`, `done`,
`cancelled`, and `error`) for clients that need progressive responses. The
protocol and SDKs live in `docs/protocol/agent-stream.md` and
`libs/agent-stream-*`. Active runs can receive a cooperative cancellation request through
`POST /api/chat/runs/{run_id}/cancel`. User-facing conversation
metadata is kept in the same database catalog, while the transcript and graph
state remain owned by LangGraph's checkpoint tables. Execution context already
has contracts for `thread_id`, `workspace_id`, `project_id`, `user_id`, and
`run_id`; workspace metadata will be persisted in a later schema version.
