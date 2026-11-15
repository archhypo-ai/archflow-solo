# archhypo-flow-agent

Conversational agent for the initial ArchHypo validation flow. Each structured
stage is a LangGraph node; the final `response_generation` stage reuses the
existing LangChain ReAct agent. The model and tools remain injected into graph
construction.

## Structure

```text
src/archhypo_flow_agent/
├── agents/          # Structured stage agents and final ReAct agent
├── backend/         # Local FastAPI chat and conversation-history API
├── cli/             # Graph utilities
├── config/          # Environment-backed settings
├── core/            # Shared graph state and contracts
├── graph/           # LangGraph workflow and stage nodes
├── observability/   # Optional tracing integrations
├── persistence/     # Checkpoint and conversation persistence
├── providers/       # LLM provider factories
├── services/        # Application-facing agent operations
├── stream/          # Validated events shared with the frontend
└── tools/           # Agent tools such as bounded public-web search
```

The graph starts with `request_routing`. New uncertainties go through discovery;
alternative or revised hypotheses reuse the active uncertainty; contextual,
out-of-scope, and ambiguous requests use `direct_response_generation` without
clearing completed results. ArchHypo runs still pass through hypothesis review,
assessment, plan generation, plan review, and `response_generation`. Discovery
uses conversation input and runtime context; it does not inspect a workspace.
Scope and implementation boundaries are documented in
[`../../docs/archhypo-flow.md`](../../docs/archhypo-flow.md).

Hypothesis formulation distinguishes initial proposals, alternatives for the
same uncertainty, and revisions. Alternatives are checked against the relevant
history: local checks reject repeated statements/titles, and the main model
compares non-identical claims semantically. A failed candidate is regenerated
at most once. The generator can also request clarification instead of proposing
a hypothesis. If no distinct proposal is found, the conversation receives a
question without a duplicate approval card, and the prior approved analysis is
preserved. The graph still has nine functional nodes; this uses the existing
direct-response node, not a fallback request classifier.

The technical planner screens the full `skills/archhypo-catalog/SKILL.md`
index, considers up to five pattern candidates and selects up to three for
Markdown reference reading. The plan then contains one to three actions and is
validated so it only uses patterns whose references were read. The skill and
its twelve Markdown references are bundled with the Python package.

## Skills gallery

The desktop Settings → Skills page reads application-wide skills directly from
`~/.archhypoflow/skills/<skill-name>/SKILL.md`. Creating a skill writes YAML front matter (`name` and
`description`), Markdown instructions, and optional text reference files. Names
must use lowercase letters, digits, and hyphens. Existing skills are never
silently overwritten. Existing skills can be edited or deleted; changes made
externally are detected before saving or deletion. The editor loads UTF-8 text
files up to 100 KB; larger, binary, hidden or linked files are listed separately
and preserved when saving. Skills with an uneditable SKILL.md can be deleted but
not saved from the editor. Skills are not stored in SQLite or loaded into agents
by this gallery. Upload and agent integration are not implemented yet.

## Provider settings

Settings → Providers → Models configures the OpenRouter API key and
model identifiers. The key is stored in the system credential store and takes
precedence over `OPENROUTER_API_KEY`; model selections are stored in
`~/.archhypoflow/providers.json` and take precedence over `OPENROUTER_MODEL`
and `SYSTEM_ONE_MODEL`. Changes to the OpenRouter key and models take effect
on the next message, including in existing conversations. Each turn uses a fixed
configuration snapshot. The public
model catalog requires no key. The System One selector queries OpenRouter's
`output_modalities=decisions` catalog and only lists entries advertising the
`/api/alpha/decisions` endpoint. Listing does not guarantee account access or
support for every decision question type. The last successful model catalogs
are cached separately in `~/.archhypoflow/cache/openrouter/general.json` and
`decisions.json`, including input and output prices. If refreshing fails, the
UI indicates that cached data may be stale.

Settings → Providers → Observability configures Langfuse and LangSmith. Keys
are stored in the system credential store, falling back to the corresponding
environment variables; enablement is stored in `providers.json`. Changes take
effect after restarting the application. Optional endpoints and project names
continue to use environment variables. Configured means keys are present, not
that credentials or provider connectivity have been verified.

## Tools gallery

Settings → Plugins → Tools lists Tavily and Exa. The enabled setting is stored
in `~/.archhypoflow/tools/<tool-id>.json`; API keys are stored in the operating
system credential store, which must be available and unlocked. Existing
`TAVILY_API_KEY` and `EXA_API_KEY` environment variables are supported as
fallbacks. Configured means a non-empty key exists, not that it was validated.
Tavily is available to direct and final response agents when enabled and
configured. Exa search is implemented but not exposed to agents yet.

## MCP gallery

Settings → Plugins → MCPs manages `~/.archhypoflow/mcp.json`. Servers can be
configured with stdio, SSE, or streamable HTTP, and manually connected to list
their tools. Adding a server does not connect it automatically. After the user
selects Connect, the application records `auto_connect: true` in `mcp.json` and
attempts to connect on subsequent backend startups. Selecting Disconnect also
removes that preference, so the server remains disconnected on later startups.
Connections run in the background and close when the backend stops; tools are not
made available to agents yet. The folder is independent of
`ARCHHYPO_FLOW_STORAGE_ROOT`.

For stdio, environment entries may reference the backend environment using
`${VARIABLE}`. Literal values entered in the form are saved in `mcp.json`; do
not put secrets there. The child inherits the MCP SDK's standard environment
and explicitly configured entries. Connecting a stdio server executes the
configured local command. For a manual test, configure `npx` with arguments
`-y` and `@modelcontextprotocol/server-everything` (this downloads and runs
third-party code; pin a version for repeatability).

## Development

```bash
cd libs/archhypo-flow-agent
uv sync --dev
uv run pytest
uv run ruff check .
```

The local API exposes `POST /api/chat`, the streaming `POST /api/chat/stream` endpoint used by the desktop UI, `GET /api/threads`, and `GET /api/threads/{thread_id}`. The streaming endpoint sends tool-call starts and results as they occur before the final reply. LangGraph checkpoints and conversation metadata share one SQLite database, defaulting to `~/.archhypoflow/runtime/checkpoints.sqlite`; override the storage root with `ARCHHYPO_FLOW_STORAGE_ROOT`. Existing databases at the previous `~/.local/share/archhypo-flow/runtime/` location are not migrated or deleted automatically.

The desktop API uses `ChatOpenRouter` from the configured provider factory. Set `OPENROUTER_API_KEY` and `SYSTEM_ONE_MODEL`, and optionally `OPENROUTER_MODEL`, in this package's `.env`; the development launcher starts the backend with this directory as its working directory. If a required setting is missing, conversation history remains available, but chat requests return a configuration error instead of a fake reply.

Request classification in the initial `request_routing` node exclusively uses the provider-neutral `SystemOneClient` contract backed by OpenRouter's decisions endpoint. Configure `SYSTEM_ONE_MODEL` with a supported decision model identifier, for example `typesafe/jev-1.14` or `microsoft/microsoft-decision-1`; the graph has no model-vendor-specific logic. `SYSTEM_ONE_ENDPOINT` and `SYSTEM_ONE_TIMEOUT` can override the endpoint and timeout. There is no LLM or deterministic fallback: a failed or invalid SystemOne response stops the turn with an explicit routing error, before any hypothesis or direct response is generated. Existing results remain unchanged, and the user message remains checkpointed. The main chat model is used only after a valid route has been selected. Structured human-review decisions resume their pending stage without calling the router again.

Global context is saved in the Tauri Store preferences file and sent as a snapshot with each chat request. Project context remains in the project's SQLite `instructions` field and is resolved through the conversation's persisted project association. The shared `agents.prompts.build_system_prompt()` function appends both contexts to the fixed prompt without storing them in checkpointed conversation messages; project context is included only for conversations belonging to that project.

Tavily public-web search is enabled when `TAVILY_API_KEY` is configured. Install its optional dependency with `uv sync --extra research` (the desktop development launcher includes this extra). The tool only accepts bounded public queries, rejects obvious secrets and local paths, and returns short excerpts rather than raw page content. Never include private code, project details, credentials, or secrets in a search query.

## Optional human approval (HITL)

Human approval is enabled by default. To skip both the hypothesis review and
assessment/technical-plan review, add this to `libs/archhypo-flow-agent/.env`:

```dotenv
HITL_ENABLED=false
```

Restart the backend (or the desktop development launcher) after changing the
file. Set `HITL_ENABLED=true`, or remove the variable, to allow approval again.
The desktop also has a **Human approval (HITL)** switch in **Settings → General**,
below **App version**. It defaults to on, persists in `localStorage` like the
theme, and is sent as `hitl_enabled` with every chat request. UI changes apply
to subsequent requests without restarting. Approval is enabled only when both
the environment setting and request preference are enabled; an omitted request
preference defaults to `true`, preserving existing API behavior.

With approval disabled, discovery, formulation, assessment, plan generation,
and the final response still run normally; no approval interrupts or synthetic
human-review history cards are produced. The option is resolved per run, not
stored in conversation checkpoints. A review already pending before the restart
still needs its existing review action to resume; subsequent gates are skipped.

## Optional observability

Tracing is disabled by default. Install both tracing integrations with
`uv sync --extra observability`, then configure either or both providers in this
package's `.env`:

```dotenv
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=archhypo-flow

LANGFUSE_ENABLED=true
LANGFUSE_SECRET_KEY=...
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

Each graph run includes its run, thread, and (when available) project IDs as
metadata. Missing credentials, unavailable optional packages, or provider
errors disable that provider without stopping chat. Shutting down the service
flushes initialized clients. Tracing providers receive model inputs and outputs;
review data retention and masking before enabling it for sensitive
conversations.

## Draw the graph

From the repository root:

```bash
uv run --project libs/archhypo-flow-agent archhypo-flow-workflow-diagram
```

This writes both the Mermaid source (`docs/architecture/archhypo-flow-agent.mmd`)
and its PNG image (`docs/architecture/archhypo-flow-agent.png`). Override the
output directory with `--output-directory`.
