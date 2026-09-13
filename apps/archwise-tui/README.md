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
or press `Ctrl+N` to create one. Existing content requires confirmation before
being discarded. Press `Esc` or `Ctrl+C` to exit.

The TUI shows animated `Connecting`, `Thinking`, and `Answering` phases while
the backend request is pending. These are visual phases only; real LangGraph
events and token streaming will be added later.

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

The backend currently uses in-memory checkpoints. Conversations disappear when
its process stops until SQLite persistence is introduced.
