# archwise-tui

Minimal Ratatui client for the local ArchWise backend.

## Run

From the repository root:

```bash
cargo run --manifest-path apps/archwise-tui/Cargo.toml
```

The TUI starts the Python backend automatically with
`uv run python -m archwise_agent.backend.server`, waits for
`GET /api/health`, and terminates only the process it started when the TUI
exits. Set `ARCHWISE_UV_BIN` when `uv` is not available under that name.

Type a message and press `Enter`. Press `Tab` to focus the conversation list;
use the arrow keys and `Enter` to switch conversations. Select `New conversation`
or press `Ctrl+N` to create one. Select a conversation and press `d` to delete
it. Both new conversation and delete actions require confirmation when needed.
Press `Esc` or `Ctrl+C` to exit.

The TUI consumes `POST /api/chat/stream` using Server-Sent Events (SSE).
`Connecting`, `Thinking`, and `Answering` phases come from the backend, and
assistant text is appended as delta events arrive.

The TUI uses Ratatui widgets (`Block`, `List`, `Paragraph`, and `Wrap`) and
keeps application state, HTTP communication, process management, and rendering
in separate modules:

```text
src/
├── main.rs
├── app.rs
├── api.rs
├── backend.rs
└── ui.rs
```

The backend stores checkpoints and conversation metadata in
`.archhypo/runtime/checkpoints.sqlite` at the monorepo root. The database is
created and migrated automatically on first startup. Set
`ARCHWISE_STORAGE_ROOT` to use another local storage directory.
