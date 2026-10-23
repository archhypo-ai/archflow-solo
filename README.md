# ArchHypo Flow

Desktop application for exploring architectural uncertainty with the ArchHypo technique.

## Structure

- `apps/archhypo-flow-desktop` — Tauri desktop application.
- `contracts` — shared data contracts.
- `docs` — project documentation.
- `libs` — reusable libraries.

The current ArchHypo workflow is documented in
[`docs/archhypo-flow.md`](docs/archhypo-flow.md).

The desktop app is a Tauri/React chat harness built with assistant-ui and a local FastAPI/LangGraph backend. The shared SSE event contract is defined in `contracts/agent-stream.schema.json`.

## Run the CLI

From the repository root, pass a prompt directly:

```bash
uv run --project libs/archhypo-flow-agent python archhypoflow_cli.py \
  "Can one server handle the projected document load?"
```

Or pass a text file; its contents are used as the prompt:

```bash
uv run --project libs/archhypo-flow-agent python archhypoflow_cli.py input.txt
```

The CLI also accepts `-` to read from standard input. It uses the settings in
`libs/archhypo-flow-agent/.env` and the same local SQLite database as the app.

Export saved ArchHypo artifacts as a JSON array with:

```bash
uv run --project libs/archhypo-flow-agent python archhypoflow_cli.py \
  --export-json > artifacts.json
```

## Run the desktop app

```bash
cd apps/archhypo-flow-desktop
npm install
npm run tauri dev
```
