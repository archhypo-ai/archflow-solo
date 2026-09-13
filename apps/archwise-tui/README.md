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

Type a message and press `Enter`. Press `Ctrl+L` while the chat is focused to
start a fresh chat without deleting the saved conversation. Press `Esc` during
generation to cancel it; `Ctrl+C` exits the TUI. Press `Tab` to focus the conversation list;
use the arrow keys and `Enter` to switch conversations. Select `New conversation`
or press `Ctrl+N` to create one. Select a conversation and press `d` to delete
it. Both new conversation and delete actions require confirmation when needed.
Press `Esc` or `Ctrl+C` to exit.

The TUI consumes `POST /api/chat/stream` using Server-Sent Events (SSE).
`Connecting`, `Thinking`, and `Answering` phases come from the backend, and
assistant text is appended as `text_delta` events arrive. Use `Up`/`Down`,
`PageUp`/`PageDown`, `Home`, `End`, or the mouse wheel to scroll the chat.
Assistant messages are rendered as Markdown using `tui-markdown`. The shared Rust protocol decoder is
provided by `libs/agent-stream-rust`.

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
