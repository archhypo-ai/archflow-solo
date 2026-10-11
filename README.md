# ArchHypo Flow

Desktop application for exploring architectural uncertainty with the ArchHypo technique.

## Structure

- `apps/archhypo-flow-desktop` — Tauri desktop application.
- `contracts` — shared data contracts.
- `docs` — project documentation.
- `libs` — reusable libraries.

The desktop app is a Tauri/React chat harness built with assistant-ui and a local FastAPI/LangGraph backend. The shared SSE event contract is defined in `contracts/agent-stream.schema.json`.

## Run the desktop app

```bash
cd apps/archhypo-flow-desktop
npm install
npm run tauri dev
```
