# ArchHypo Flow Desktop

Tauri and React desktop chat harness using the latest `@assistant-ui/react` package. The interface supports English and Brazilian Portuguese, detects the system language on first launch, and remembers the selected language. Appearance can follow the system preference or be fixed to Day or Night, using Tokyo palette tokens centralized in `src/theme/tokens.css`. The account menu provides a language submenu and a Settings dialog. The sidebar can create and list local projects; project names, icons, colors, and additional instructions are stored locally. General settings also store global agent instructions locally. The current demo chat does not yet apply project or global instructions to an agent. On Linux, the Tauri entry point disables WebKitGTK's DMA-BUF renderer by default to avoid blank windows on affected graphics drivers; an explicitly set `WEBKIT_DISABLE_DMABUF_RENDERER` value is preserved.

The desktop app starts the local FastAPI chat service alongside Vite during development. Chat turns use OpenRouter, are checkpointed in SQLite, and are restored from the sidebar. The API reads `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` from `libs/archhypo-flow-agent/.env`; without a key, history remains available and chat reports a configuration error. Projects and instructions remain local UI settings and are not sent to the agent yet.

The desktop's default chat backend is `libs/archhypo-flow-agent`. Its default graph now runs every message through the ArchHypo discovery, hypothesis formulation, assessment, and technical planning stages before the existing final response stage. The former single-node chat graph is no longer used as the default workflow; the response-generation agent remains only to produce the final user-facing reply. See [`docs/archhypo-flow.md`](../../docs/archhypo-flow.md).

By default, the database is stored at `~/.local/share/archhypo-flow/runtime/checkpoints.sqlite`. Override the storage root with `ARCHHYPO_FLOW_STORAGE_ROOT`.

## Development

Install the Python agent dependencies once, then run the desktop app:

```bash
uv sync --project libs/archhypo-flow-agent --dev
cd apps/archhypo-flow-desktop
npm install
npm run tauri dev
```

The Tauri dev command starts the API and Vite together. To run only the frontend, use `npm run dev`. To run the API manually (from its package directory, so it loads that directory's `.env`):

```bash
cd libs/archhypo-flow-agent
uv run python -m uvicorn archhypo_flow_agent.backend.app:app --host 127.0.0.1 --port 8765
```

Build the frontend with:

```bash
npm run build
```
