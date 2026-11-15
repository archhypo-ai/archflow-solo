# ArchHypo Flow Desktop

Tauri and React desktop chat harness using the latest `@assistant-ui/react` package. The interface supports English and Brazilian Portuguese, detects the system language on first launch, and remembers the selected language. Appearance can follow the system preference or be fixed to Day or Night, using Tokyo palette tokens centralized in `src/theme/tokens.css`. The account menu provides a language submenu and a Settings dialog. The sidebar can create and list local projects; project names, icons, colors, and additional instructions are stored locally. General settings also store global agent instructions locally. The current demo chat does not yet apply project or global instructions to an agent. On Linux, the Tauri entry point disables WebKitGTK's DMA-BUF renderer by default to avoid blank windows on affected graphics drivers; an explicitly set `WEBKIT_DISABLE_DMABUF_RENDERER` value is preserved.

The desktop app starts the local FastAPI chat service alongside Vite during development. Chat turns use OpenRouter, are checkpointed in SQLite, and are restored from the sidebar. The API reads `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` from `libs/archhypo-flow-agent/.env`; without a key, history remains available and chat reports a configuration error. Projects and instructions remain local UI settings and are not sent to the agent yet.

The desktop's default chat backend is `libs/archhypo-flow-agent`. Its default graph now runs every message through the ArchHypo discovery, hypothesis formulation, assessment, and technical planning stages before the existing final response stage. The former single-node chat graph is no longer used as the default workflow; the response-generation agent remains only to produce the final user-facing reply. See [`docs/archhypo-flow.md`](../../docs/archhypo-flow.md).

By default, the database is stored at `~/.archhypoflow/runtime/checkpoints.sqlite`. Override the storage root with `ARCHHYPO_FLOW_STORAGE_ROOT`. Databases at the previous `~/.local/share/archhypo-flow/runtime/` location are not migrated or deleted automatically.

## Human approval (HITL)

**Settings → General** includes a **Human approval (HITL)** switch immediately
below **App version**. It is on by default and saved in `localStorage`, just
like the theme. Switching it off skips hypothesis and technical-plan approval
pauses for subsequent requests without restarting the app. Already pending
reviews still require their review action to resume.

Each chat request sends the saved preference as `hitl_enabled`.
`HITL_ENABLED=false` in the backend's `.env` always disables approval, even if
the visual switch is on. Neither option creates synthetic approval history.

Run the preference tests with `npm test` (Node.js 22.18+).

## Interface translations

Application-authored interface text belongs in both `src/i18n/locales/en.json` and
`src/i18n/locales/pt-BR.json`, including accessible labels, placeholders, and
examples. Use `useTranslation()` instead of choosing language-specific strings
in components. `npm test` and `npm run build` check catalog parity, literal
translation keys, and common hard-coded JSX text and labels. These static checks
cannot detect every dynamically assembled string or translate content supplied
by users, models, MCP servers, or backend errors; review those paths separately.

## Development

Install the Python agent dependencies once, then run the desktop app:

```bash
uv sync --project libs/archhypo-flow-agent --dev
cd apps/archhypo-flow-desktop
npm install
npm run tauri dev
```

The Tauri dev command starts the API and Vite together; the launcher installs the optional `research` and `observability` extras. Tracing remains disabled unless LangSmith or Langfuse is enabled in `libs/archhypo-flow-agent/.env`; see the agent README for the variables. To run only the frontend, use `npm run dev`. To run the API manually (from its package directory, so it loads that directory's `.env`):

```bash
cd libs/archhypo-flow-agent
uv run --extra research --extra observability python -m uvicorn archhypo_flow_agent.backend.app:app --host 127.0.0.1 --port 8765
```

Build the frontend with:

```bash
npm run build
```
